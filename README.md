# A Travel Planner powered by AutoGen Agents

## 🌟 Motivation

Planning a trip can be overwhelming, especially when you're unfamiliar with the destination. With endless options for activities, dining, and sightseeing, it's challenging to know where to start. 

## Purpose

This Streamlit app leverages the power of AutoGen agents to provide a curated travel guide with personalized recommendations for hotels, airports, must-see places, and dining options.

### Why is this important?

- Travellers spend over 5 hours on average with travel content in the 45 days prior to booking (source: [Expedia Group Research, July 2023 ](https://www.expediagroup.com/investors/news-and-events/financial-releases/news/news-details/2023/TRAVELERS-SPEND-OVER-5-HOURS-RESEARCHING-TRIPS-ON-AVERAGE---LONGER-THAN-FLYING-FROM-LOS-ANGELES-TO-WASHINGTON-DC---ACCORDING-TO-EXPEDIA-GROUP-RESEARCH/default.aspx#:~:text=July%2025%2C%202023%2C%20SEATTLE%20%E2%80%94,45%20days%20prior%20to%20booking.)).

- Overall, 22% of U.S. adults find that creating their trip itinerary is one of the most frustrating parts of planning and booking a trip, and almost 40% of Gen Z believe less time dedicated to planning and booking would enable them to get into vacation-mode feeling energized, rather than starting their trip exhausted.  (source: [Priceline Press Center, Feb 2024 ](https://press.priceline.com/new-priceline-research-finds-average-traveler-spends-two-full-work-days-to-plan-and-book-trips/))

In this scenario, the impact intended with such an app comes from:

- **Time-saving**: eliminating the hours spent researching and organizing activities by providing a curated list of suggestions.
- **Personalization**: adapting the suggestions based on the user's specific information, ensuring a unique experience.
- **Discovery**: suggesting hidden gems and must-see attractions.
- **Optimization**: ensure you make the most out of your trip without feeling rushed.

## 🎥  Demo

### Trip to Orlando, USA

![alt text](gifs_imgs/orlando_romantic_trip2-1.gif)

### Trip to Recife, Brazil
![alt text](gifs_imgs/recife-wit-the-kids-edited-1.gif)
## 🚀 Features

- **City Selection**: Input the city you plan to visit.
- **Arrival and Departure Dates**: Provide your travel dates, and the app will create a plan that fits your schedule.
- **Additional considerations**: Provide additional considerations that will be used to customize your travel plan (such as preferred dining options)
- **Activity Recommendations**: Suggestions include popular tourist spots, dining options, cities hidden gems, and more.

## 🛠️ How It Works

1. **User Inputs**: The user enters the destination city, along with the arrival and departure dates.
2. **Agent Activation**: AutoGen agents analyze the input and gather relevant information about the destination.
3. **Itinerary Generation**: The app constructs a personalized suggestions plan for daily activities and recommendations.
4. **Review and Customize**: Users can review the generated suggestions and make any desired adjustments directly within the app.

## 📦 Installation

To run this app locally:

1. **Clone the repository**:
    ```bash
    git clone [https://github.com/yourusername/travel-plan-generator.git](https://github.com/LiviaPimentel/autogen-travelplanner.git)
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3. **Create a .env file with the following**:
    ```bash
    pip install -r requirements.txt
    ```   

4. **Run the app**:
    ```bash
    OPENAI_BASE_URL=[]
    OPENAI_API_KEY=[]
    RAPID_API_KEY=[]
    TAVILY_API_KEY=[]
    ```
    OBS:
   - To obtain a RAPID_API_KEY api key, checkout this link (there is a free version): [API by ApiDojo](https://rapidapi.com/apidojo/api/booking)
   - To obtain a TAVILY_API_KEY, check: [Tavily Research](https://tavily.com/)

## 🧑‍💻 Technologies Used

- **Streamlit**: For building the interactive web app.
- [AutoGen](https://microsoft.github.io/autogen/docs/Getting-Started/#:~:text=AutoGen%20is%20an%20open%2Dsource,like%20PyTorch%20for%20Deep%20Learning.): Python-based framework from Microsoft Research that allows developers to create multi-agent systems for AI applications.
- **Docker**: For deployment (Work in Progress)
- **API's**:
    - [Booking API](https://rapidapi.com/apidojo/api/booking) , for searching hotel options corresponding to checkin/out dates, travel purpose, etc (**see tools/get_list_of_locations**) method.
    - [Tavily Research](https://tavily.com/) , an automated research tool that helps users save time and energy researching topics.
    - [Geopy API](https://pypi.org/project/geopy/), for getting geographical coordinates from airports and hotels
    - [Folium](https://pypi.org/project/folium/) for plotting maps
- **Airports Database**: [The Global Airports Database](http://www.partow.net/miscellaneous/airportdatabase/index.html)

## 🤝 Contributing

Feel free to fork the repository and submit a pull request.

## 📝 License

This project is licensed under the Apache V2 License. (Please, check [License](https://github.com/LiviaPimentel/autogen-travelplanner/blob/main/LICENSE))

---

🌍✈️
