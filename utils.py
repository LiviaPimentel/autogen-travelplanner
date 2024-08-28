from autogen import UserProxyAgent
from openai import OpenAI
import streamlit as st
import asyncio
from datetime import date
import yaml
import os

with open('conf/tasks_config.yml', 'r') as file:
    tasks_config = yaml.safe_load(file)
with open('conf/agents_config.yml', 'r') as file:
    agents_config = yaml.safe_load(file)

def process_task(task_name, **kwargs):
    """
    Process a task by rendering its template with provided keyword arguments.

    Args:
        task_name (str): The name of the task to be processed.
        **kwargs: Variable keyword arguments representing input values for the task.

    Returns:
        str: The rendered task template with the provided inputs.

    Raises:
        ValueError: If the task is not found in the configuration or if required inputs are missing.
    """
    # Retrieve the task template and input names from the configuration
    task_info = tasks_config.get(task_name)
    if not task_info:
        raise ValueError(f"Task '{task_name}' not found in the configuration.")
    
    task_template = task_info['task_template']
    input_names = task_info['inputs']
    
    # Ensure all required inputs are provided
    for input_name in input_names:
        if input_name not in kwargs:
            raise ValueError(f"Missing input for '{input_name}' in the task.")
    
    # Prepare keyword arguments for formatting
    formatted_kwargs = {input_name: kwargs.get(input_name, '') for input_name in input_names}
    
    # Render the task template with the provided keyword arguments
    return task_template.format(**formatted_kwargs)

def render_task(task_name, user_input_dictionary):
    """
    Render a task by processing it with user-provided input values.

    Args:
        task_name (str): The name of the task to be rendered.
        user_input_dictionary (dict): A dictionary of user inputs for the task.

    Returns:
        str: The rendered task content.

    Raises:
        KeyError: If a required input is missing in the user input dictionary.
    """
    task_content = tasks_config.get(task_name)
    input_dictionary = {}
    for key_input in task_content['inputs']:
        input_dictionary[key_input] = user_input_dictionary[key_input]
        
    return process_task(task_name, **input_dictionary)

def render_agent_sys_msg(agent_name):
    """
    Retrieve the system message for a given agent.

    Args:
        agent_name (str): The name of the agent.

    Returns:
        str: The system message associated with the specified agent.

    Raises:
        KeyError: If the agent is not found in the configuration.
    """
    agent_content = agents_config.get(agent_name)
    return agent_content['system_message']

def get_task_objective(task_name):
    """
    Retrieve the objective of a specific task.

    Args:
        task_name (str): The name of the task.

    Returns:
        str: The objective of the task.

    Raises:
        ValueError: If the task does not have an objective in the configuration.
    """
    task_content = tasks_config.get(task_name)
    if 'objective' in task_content.keys():
        return task_content['objective']
    else:
        raise ValueError(f"The task '{task_name}' does not have an objective")
        
def generate_summary_with_llm(conversation_history, task_objective, model="gpt-4"):
    """
    Uses a LLM to reflect on the conversation history and produce an 
    output that achieves the task objective.

    Parameters:
        conversation_history (list): List of conversation messages.
        task_objective (str): The desired task objective to be achieved.
        model (str): The LLM model to be used (e.g., "gpt-4").

    Returns:
        str: The LLM-generated output that satisfies the task objective.
    """
    # Construct the prompt with conversation history and task objective
    prompt = """Given the following conversation history, please reflect 
    on the task objective and produce an output that achieves it. 
    The output must be as detailed as possible, not leaving behind 
    important information, nor adding new information:\n\n"""
    
    for message in conversation_history:
        prompt += f"User: {message['content']}\n"

    prompt += f"""\nTask Objective: {task_objective}\n\nPlease provide the 
    final output below:\n"""

    client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    # Call the LLM (GPT-4 or other model)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0,
    )

    # Extract the content from the LLM response
    final_output = response.choices[0].message.content
    
    return final_output

def create_agent(agent_class, name, system_message, llm_config, tools, termination_check):
    """
    Create an instance of a given agent class and register tools for it.

    Args:
        agent_class (type): The class of the agent to be instantiated.
        name (str): The name of the agent.
        system_message (str): The system message to configure the agent.
        llm_config (dict): Configuration for the LLM.
        tools (dict): A dictionary of tools to register, where each key is the tool's name and each value is a dictionary containing tool details.
        termination_check (bool): Flag to check if termination messages are enabled.

    Returns:
        agent: An instance of the agent class with tools registered.
    """
    agent = agent_class(
        name=name,
        system_message=system_message,
        llm_config=llm_config,
        is_termination_msg=termination_check
    )
    for tool_name, tool_dict in tools.items():
        key = list(tool_dict.keys())[0]
        agent.register_for_llm(name=tool_name, description=tool_dict[key])(key)
    return agent

def create_user_proxy_agent(name, llm_config, tools, termination_check):
    """
    Create an instance of UserProxyAgent and register tools for it.

    Args:
        name (str): The name of the user proxy agent.
        llm_config (dict): Configuration for the LLM.
        tools (dict): A dictionary of tools to register, where each key is the tool's name and each value is a dictionary containing tool details.
        termination_check (bool): Flag to check if termination messages are enabled.

    Returns:
        user_proxy: An instance of UserProxyAgent with tools registered.
    """
    user_proxy = UserProxyAgent(
        name=name,
        human_input_mode="NEVER",
        llm_config=llm_config,
        code_execution_config=False,
        is_termination_msg=termination_check
    )
    for tool_name, tool_dict in tools.items():
        key = list(tool_dict.keys())[0]
        user_proxy.register_for_execution(name=tool_name)(key)
    return user_proxy

def generate_sequence_of_tasks(
                               spinner_message, 
                               user_agent,
                               chats_list, 
                               manager_agent, 
                               critic_messages,
                               objective
                               ):
    """
    Generate a sequence of tasks involving chat initiation and summary generation.

    Args:
        spinner_message (str): Message to display while tasks are running.
        user_agent: The user agent instance to initiate chats.
        chats_list (list): List of chats to initiate.
        manager_agent: The manager agent instance to manage chat messages.
        critic_messages (list): List of critic messages to summarize.
        objective (str): The objective for the summary generation.

    Returns:
        tuple: A tuple containing the summary of critic messages and the results of chat initiation.
    """
    # Create an event loop: this is needed to run asynchronous functions
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    with st.spinner(spinner_message):
        
        async def initiate_chat():
            chat_results = user_agent.initiate_chats(chats_list)
            chat_messages = manager_agent.chat_messages[user_agent]
            return chat_results, chat_messages
        
        results = loop.run_until_complete(initiate_chat())
        loop.close()
        
        message_task = generate_summary_with_llm(critic_messages, objective)
        
    return message_task, results

def hotels_colormap():
    """
    Return a color mapping for hotel ratings.

    Returns:
        dict: A dictionary mapping rating categories to colors.
    """
    color_mapping = {
        "Excellent": "green",
        "Okay": "orange",
        "Pleasant": "purple",
        "Good": "blue",
        "Fair": "gray",
    }
    return color_mapping
        