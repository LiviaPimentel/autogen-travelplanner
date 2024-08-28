# Standard library imports
import os
from datetime import date

# Third-party library imports
import pandas as pd
from PIL import Image
import streamlit as st
from dotenv import load_dotenv
from autogen import (AssistantAgent, UserProxyAgent, GroupChatManager, GroupChat)

# Local application imports
from utils import (render_task, render_agent_sys_msg, create_agent,
                   get_task_objective, create_user_proxy_agent,
                   generate_sequence_of_tasks, hotels_colormap)
from tools import (get_list_of_locations, plot_hotels_on_map, search_tavily)

# Load environment variables
load_dotenv("./.env")

critic_messages = []
websearch_critic_messages = []
# Airports dataframe
df = pd.read_csv("csv_files/airports.csv")

countries = df['Country'].unique()

class TrackableCriticAgent(AssistantAgent):
    def _process_received_message(self, message, sender, silent):
        critic_messages.append(message)
        return super()._process_received_message(message, sender, silent)    

class TrackableWebSearchCriticAgent(AssistantAgent):
    def _process_received_message(self, message, sender, silent):
        websearch_critic_messages.append(message)
        return super()._process_received_message(message, sender, silent)    

# Common termination check function
termination_check = lambda x: (
    x is not None and isinstance(x, dict) and 
    isinstance(x.get("content", ""), str) and 
    x.get("content", "").find("TERMINATE") >= 0
)

# setup page title and description
st.set_page_config(page_title="AutoGen Chat app", page_icon="✈️", layout="wide")
image_path = "gifs_imgs/logo.png"  # Replace with the path to your image

# Create a custom title layout
image = Image.open(image_path)

# Create a layout with two columns
col1, col2 = st.columns([1, 5])  # Adjust the proportions to fit your needs

with col1:
    st.image(image, width=200)  # Adjust the width to fit your needs

with col2:
    st.title("Autogen Travel Planner")

st.markdown("""**We will help you plan your travel with a workforce of Autogen Agents!**""")
st.markdown("""Tasks:""")
st.markdown("- Hotel options according to your needs")
st.markdown("- Airport options in the city")
st.markdown("- Must-see attractions in the city")
st.markdown("- The best dining places according to your preferences")
# add placeholders for selected model and key
selected_model = "gpt-4-1106-preview"
selected_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")

llm_config = {
            #"request_timeout": 600,
            "config_list": [
                {"model": selected_model, "api_key": selected_key, "base_url":base_url},
            ],
            "seed": 41,  # seed for reproducibility
            "temperature": 0,  # temperature of 0 means deterministic output
            "cache_seed": None,
}

# setup main area: user input and chat messages
with st.container():
    
    travel_purpose = st.selectbox(
        "Select your travel purpose:",
        ('leisure','business'),
    )
    
    country_option = st.selectbox(
        "Select your destination country:",
        sorted(tuple(countries)),
    )
    
    cities_options = df.query("Country == @country_option")['City/Town'].unique()
    
    city_name = st.selectbox(
        "Select your destination city:",
        sorted(tuple(cities_options)),
    )
    
    number_of_kids = st.selectbox(
        "Number of kids travelling with you:",
        (0,1,2,3,4,5,6,7,8,9,10),
    )
    
    number_of_guests = st.selectbox(
        "Number of guests (for hotel options):",
        (1,2,3,4,5,6,7,8,9,10),
    )
    
    number_of_rooms = st.selectbox(
        "Number of rooms (for hotel options):",
        (1,2,3,4,5,6,7,8,9,10),
    )
    
    children_age = st.text_input("Children age, separated with comma")
    
    additional_considerations = st.text_input("""Additional considerations. 
                                              e.g: 'Planning honeymoon trip/Visiting the city for the first time.'""")
    
    dining_options = st.multiselect(
        "When searching for dining options, what type of food do you prefer?",
        ["Vegan", "Seafood", 
         "Traditional cuisine from the city", 
         "Meat","Pasta","Japanese"]
    )
    
    arrival_date = st.date_input("Arrival Date", value=date.today())
    departure_date = st.date_input("Departure Date", value=date.today())
    
    submit_button = st.button("Submit")

    if submit_button and city_name and arrival_date and departure_date:
        
        if additional_considerations == '' or len(dining_options) == 0:
            if additional_considerations == '' and len(dining_options) != 0:
                error_msg = 'Please, provide additional considerations (details)'
            else: 
                error_msg = 'Please, select at least one dining option'
            if additional_considerations == '' and len(dining_options) == 0:
                error_msg = 'Please, provide additional consideration and select at least one dining option'
            st.error(error_msg, icon="🚨")
        
        else: 
            user_input = f"""
            - City: {city_name}, \n
            - Country: {country_option}, \n
            - Arrival Date: {arrival_date}, \n
            - Departure date: {departure_date}, \n
            - Quantity of children travelling: {number_of_kids}, \n
            - Children age: {children_age} , \n 
            - Number of guests: {number_of_guests} , \n 
            - Number of rooms: {number_of_rooms} , \n 
            - Travel purpose: {travel_purpose}
            """
            # DEFINING TASKS
            generate_hotels_table = render_task('generate_hotels_table',{'user_input':user_input})
            generate_hotels_text = render_task('generate_hotels_text',{})
            generate_hotels_text_objective = get_task_objective('generate_hotels_text')
            get_locations_tuple = render_task('get_locations_tuple',{})
            generate_hotels_chart = render_task('generate_hotels_chart',{'city_name':city_name,
                                                         'country_option':country_option})
            
            search_places = render_task('search_places',{'city_name':city_name,
                                                'country_option':country_option,
                                                'additional_considerations':additional_considerations})
            
            search_places_objective = get_task_objective('search_places')

            generate_table_places = render_task('generate_table_places',{})

            search_dining_places=render_task('search_dining_places',{'city_name':city_name,
                                                                     'country_option':country_option,
                                                      'dining_options':dining_options})
            
            generate_dining_places_text = render_task('generate_dining_places_text',{})
            
            generate_dining_places_text_objective = get_task_objective('generate_dining_places_text')
            
            # DEFINING TOOLS DICTIONARIES
            tools_task_dict={
                        "get_list_of_locations": {get_list_of_locations:
                            """Retrieves a list of locations (e.g., hotels) 
                                within a city for given arrival and departure dates, 
                                and returns the data as a Markdown table including 
                                latitude, longitude, hotel name, address, and review score"""},
                        "plot_hotels_on_map": {plot_hotels_on_map:
                            """Plots hotel locations on a folium map.
                            Given a City name, Country name, and a List of tuples , 
                            each containing (latitude,longitude, hotel_name, booking url)"""},
                    }

            tools_web_search_dict = {"search_tavily": {search_tavily:"""Search for information on the web"""}}

            # create an AssistantAgent instance named "assistant"
            assistant = create_agent(AssistantAgent, 
                                     "assistant", 
                                     render_agent_sys_msg('travel_assistant'), 
                                     llm_config, 
                                    tools_task_dict,
                                    termination_check)
            
            websearch_assistant = create_agent(AssistantAgent, 
                                            "websearch_assistant", 
                                            render_agent_sys_msg('websearch_assistant'),
                                            llm_config, 
                                            tools_web_search_dict,
                                            termination_check)

            user_proxy = create_user_proxy_agent("user", llm_config, 
                                                tools_task_dict, termination_check)
            websearch_user_proxy = create_user_proxy_agent("websearch_user", llm_config, tools_web_search_dict, termination_check)

            user = UserProxyAgent(name="User", human_input_mode="NEVER", is_termination_msg=termination_check, code_execution_config=False)
            websearch_user = UserProxyAgent(name="websearch_user", human_input_mode="NEVER", is_termination_msg=termination_check, code_execution_config=False)
            user.register_for_execution(name="get_list_of_locations")(get_list_of_locations)
            user.register_for_execution(name="plot_hotels_on_map")(plot_hotels_on_map)
            websearch_user.register_for_execution(name="search_tavily")(search_tavily)
            
            critic = TrackableCriticAgent(
            name="Critic",
            system_message=render_agent_sys_msg('critic'),
                    llm_config=llm_config,
            )
            
            websearch_critic = TrackableWebSearchCriticAgent(
            name="WebSearchCritic",
            system_message=render_agent_sys_msg('websearch_critic'),
                    llm_config=llm_config,
            )
            
            groupchat_websearch = GroupChat(agents=[websearch_user_proxy, websearch_assistant, websearch_critic], 
                                        messages=[], 
                                        max_round=5,
                                        allow_repeat_speaker=False)
            
            groupchat = GroupChat(agents=[user_proxy, assistant, critic], 
                                        messages=[], 
                                        max_round=5,
                                        allow_repeat_speaker=False)
            
            manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)
            web_search_manager = GroupChatManager(groupchat=groupchat_websearch, llm_config=llm_config)

            if "chat_initiated" not in st.session_state:
                st.session_state.chat_initiated = False  # Initialize the session state
            
            spinner_message = 'Step 1/3: Curating your travel adventure—finding the best airports and hotels... 🌍✨'
            
            if not st.session_state.chat_initiated:
                
                chats_list=[
                            {"recipient": assistant, "message": generate_hotels_table, "summary_method": "last_msg"},
                            {"recipient": manager, "message": generate_hotels_text, "summary_method": "last_msg"},
                            {"recipient": assistant, "message": get_locations_tuple, "summary_method": "last_msg"},
                            {"recipient": assistant, "message": generate_hotels_chart, "summary_method": "reflection_with_llm"},  
                        ]
                message_task,results = generate_sequence_of_tasks(spinner_message,user,
                                                          chats_list,manager,
                                                          critic_messages,
                                                          generate_hotels_text_objective)
                st.session_state.chat_messages = results
                st.session_state.chat_initiated = True  # Set the state to True after running the chat

            if st.session_state.get("chat_messages"):
                print('Printing on frontend:')
                message_st = st.chat_message("ai")
                message_st.write(message_task)
                
                path_to_html = "./hotels_map_run.html" 
                # Read file and keep in variable
                with open(path_to_html,'r') as f: 
                    html_data = f.read()
                ## Show in webpage
                st.header("Hotels available and Airport options in the destiny city:")
                color_mapping = hotels_colormap()
                st.markdown("Color map: :green[Excellent] :orange[Okay] :violet[Pleasant] :blue[Good] :gray[Fair]")
                st.components.v1.html(html_data,height=500)
    
            ## STEP 2: MUST-SEE PLACES
            spinner_message = 'Step 2/3: Unveiling the gems of your destination—finding the must-see spots... 🌟🏙️'
            chats_list=[
                        {"recipient": websearch_assistant, 
                            "message": search_places, "summary_method": "last_msg"},
                        {"recipient": web_search_manager, 
                            "message": generate_table_places, "summary_method": "reflection_with_llm"}
                        ]
            
            message_task,results = generate_sequence_of_tasks(spinner_message,websearch_user,
                                                          chats_list,web_search_manager,
                                                          websearch_critic_messages,
                                                          search_places_objective)
            
            st.session_state.chat_messages_step2 = results
            
            if st.session_state.get("chat_messages_step2"):
                print('Printing on frontend:')
                message_st = st.chat_message("ai")
                # Printing result from first task: Hotels
                message_st.write(message_task)

            ## STEP 3: DINING OPTIONS
            spinner_message = 'Step 3/3: Savoring the flavors—discovering the must-try dining spots... 🍽️🍷'
            chats_list=[
                {"recipient": websearch_assistant, 
                    "message": search_dining_places, "summary_method": "last_msg"},
                {"recipient": web_search_manager, 
                    "message": generate_dining_places_text, "summary_method": "reflection_with_llm"}
            ]
            
            websearch_critic_messages = []
            message_task,results = generate_sequence_of_tasks(spinner_message,websearch_user,
                                                          chats_list,web_search_manager,
                                                          websearch_critic_messages,
                                                          generate_dining_places_text)
            
            st.session_state.chat_messages_step3 = results  
              
            if st.session_state.get("chat_messages_step3"):
                print('Printing on frontend:')
                message_st = st.chat_message("ai")
                # Printing result from first task: Hotels
                message_st.write(message_task)
                st.stop()

# stop app after termination command
st.stop()