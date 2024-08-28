import requests
from typing import List, Tuple
from geopy.geocoders import Nominatim
from typing_extensions import Annotated
import folium
from dotenv import load_dotenv
import pandas as pd
import os
from tavily import TavilyClient
import html_to_json
import json
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

load_dotenv('./.env')

LIST_BY_MAP_URL = "https://apidojo-booking-v1.p.rapidapi.com/properties/list-by-map"
LIST_BY_MAP_HEADERS = {
    'x-rapidapi-host': "apidojo-booking-v1.p.rapidapi.com",
    'x-rapidapi-key': os.getenv("RAPID_API_KEY")
}

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def get_city_bbox(city_name: Annotated[str, "Name of the city"],
                  country_name: Annotated[str,"Name of the country"]) -> str:
    """
    Retrieve the bounding box for a specified city and country.

    Args:
        city_name (str): The name of the city.
        country_name (str): The name of the country.

    Returns:
        str: A string representing the bounding box coordinates in a format suitable for queries.

    Raises:
        AttributeError: If the geocoding service does not return a bounding box.
    """
    geolocator = Nominatim(user_agent = "abcd")
    location = geolocator.geocode(f"{city_name}, {country_name}")
    bounding_box = location.raw['boundingbox']
    
    return "%2C".join(bounding_box)


def get_list_of_locations(city_name: Annotated[str, "Name of the city"],
    country_name : Annotated[str, "Name of the country"],
    travel_purpose: Annotated[str, "Travel purpose. Can be either leisure or business"],
    arrival_date: Annotated[str, "String representing arrival date (Year-Month-Day)"],
    departure_date: Annotated[str,"String representing departure date (Year-Month-Day)"],
    children_qty: Annotated[int, "Integer representing quantity of children travelling"],
    children_age: Annotated[str, "String representing the ages of each children separated with comma. E.g: 5,7"],
    guest_qty: Annotated[int, "Integer representing the quantity of guests"],
    room_qty: Annotated[int, "Integer representing the quantity of rooms"]) -> str:
    """
    Retrieve and format a list of hotel locations based on specified criteria.

    Args:
        city_name (str): The name of the city.
        country_name (str): The name of the country.
        travel_purpose (str): The purpose of travel, either "leisure" or "business".
        arrival_date (str): Arrival date in the format "Year-Month-Day".
        departure_date (str): Departure date in the format "Year-Month-Day".
        children_qty (int): Quantity of children travelling.
        children_age (str): Ages of the children separated by commas (e.g., "5,7").
        guest_qty (int): Quantity of guests.
        room_qty (int): Quantity of rooms.

    Returns:
        str: A Markdown-formatted table of hotel options based on the provided criteria.

    Raises:
        KeyError: If the response from the API does not contain the expected fields.
    """
    
    list_by_map_querystring = {
    "search_id":"none",
    "children_age": "" if children_qty == 0 else children_age,
    "price_filter_currencycode":"USD",
    "languagecode":"en-us",
    "travel_purpose":travel_purpose,
    "categories_filter":"class%3A%3A1%2Cclass%3A%3A2%2Cclass%3A%3A3",
    "children_qty": "" if children_qty == 0 else str(children_qty),
    "order_by":"popularity",
    "guest_qty":str(guest_qty),
    "room_qty":str(room_qty),
    "departure_date":departure_date,
    "bbox":get_city_bbox(city_name=city_name, country_name=country_name),
    "arrival_date":arrival_date
    }
    
    list_by_map_response = requests.request("GET", 
                                        LIST_BY_MAP_URL,
                                        headers=LIST_BY_MAP_HEADERS, 
                                        params=list_by_map_querystring).json()
    
    data = list_by_map_response['result']

    columns = [
    'latitude', 'longitude', 'url', 'hotel_name', 
    'address', 'review_score_word', 'checkin', 'checkout',
    'price_breakdown'
    ]
    
    df = pd.DataFrame(data, columns=columns)
    
    df['Float-Price'] = df['price_breakdown'].apply(lambda x: x['all_inclusive_price'])
    df['All-Inclusive-Price'] = df['price_breakdown'].apply(lambda x: str(x['currency'])  + ' ' + str(x['all_inclusive_price']))
    
    # Keeping only the most interesting columns
    df.drop('Float-Price',axis=1,inplace=True)
    # Saving in csv for later inspection
    df.to_csv('csv_files/booking_options.csv',index=False)
    
    df=df.query("review_score_word == 'Fair' | review_score_word == 'Good' | review_score_word == 'Pleasant'|  review_score_word == 'Okay' | review_score_word == 'Excellent'")
    df=df.drop('price_breakdown',axis=1)
    
    # For testing purposes, it might be interesting to comment all above and run only this:
    # df=pd.read_csv('files/booking_options.csv').query("review_score_word == 'Fair' | review_score_word == 'Good' | review_score_word == 'Pleasant'|  review_score_word == 'Okay' | review_score_word == 'Excellent'")
    # df=df[[
    # 'latitude', 'longitude', 'url', 'hotel_name', 
    # 'address', 'review_score_word', 'checkin', 'checkout',
    # 'price_breakdown','All-Inclusive-Price'
    # ]]
    return df.to_markdown(tablefmt="grid")


def plot_hotels_on_map(city_name: Annotated[str,"""String with the city name"""],
    country_name: Annotated[str,"""String with the country name"""],
    locations: Annotated[List[Tuple],"""List of tuples containing latitude, 
                        longitude, name of hotel, hotel link, review_score_word. Example: locations= [
    (9.0, -84.0, "HOTEL NAME", "HOTEL_URL", "HOTEL_RATING")...]
    """], 
                       map_center=None):
    """
    Plots hotel locations on a folium map.

    Parameters:
    - locations: List of tuples [(latitude, longitude, hotel_name, url), ...]
    - map_center: Tuple (latitude, longitude) to center the map, defaults to the mean of the locations
    - zoom_start: Initial zoom level for the map, defaults to 13

    Returns:
    - folium.Map object with the plotted locations
    """

    # Filtering the airport by city
    df = pd.read_csv("csv_files/airports.csv")
    df=df[df["Country"] == country_name.upper()]
    df=df[df["City/Town"] == city_name.upper()]
    print(f"City Name = {city_name.upper()}")
    
    # If no map center is provided, center the map at the mean of the locations
    if not map_center:
        mean_lat = sum([loc[0] for loc in locations]) / len(locations)
        mean_lng = sum([loc[1] for loc in locations]) / len(locations)
        map_center = (mean_lat, mean_lng)

    # Create a folium map centered around the provided coordinates
    my_map = folium.Map(location=map_center, zoom_start=13)

    # Mapping according to hotel review score
    color_mapping = {
        "Excellent": "green",
        "Okay": "orange",
        "Pleasant": "purple",
        "Good":"blue",
        "Fair":"gray",
        # Add more mappings as needed
    }
    
    # Add markers for each location with popup containing hotel name and link
    for lat, lng, hotel_name, url, review_score_word in locations:
        folium.Marker(
            location=(lat, lng),
            popup=f"<b>{hotel_name} - Review: {review_score_word}</b><br><a href='{url}' target='_blank'>Booking Link</a>",
            icon=folium.Icon(color=color_mapping.get(review_score_word,
                                                     "black"), icon='hotel', prefix='fa')
        ).add_to(my_map)
    # Add markers for each location corresponding to airports     

    df['IATA Code'] = df['IATA Code'].fillna("N/A")
    # Counter for "N/A" occurrences
    na_counter = 1
    # Iterate over the DataFrame and modify "N/A" entries
    for index, value in df['IATA Code'].items():
        if value == "N/A":
            df.at[index, 'IATA Code'] = f"N/A {na_counter}"
            na_counter += 1
    
    for iata_code in df['IATA Code'].values:
        folium.Marker(
            location=(df[df['IATA Code'] == iata_code]['Latitude Decimal Degrees'],
                      df[df['IATA Code'] == iata_code]['Longitude Decimal Degrees']),
            popup=f"Airport: {df[df['IATA Code'] == iata_code]['Airport Name'].values[0]} \n - {iata_code} ",
            icon=folium.Icon(color="red", icon='plane', prefix='fa')
        ).add_to(my_map)

    my_map.save("hotels_map_run.html")
    
    return (f"""SUCCESS: Hotel options have been successfully plotted on a folium map"""
            f"Corresponding city: {city_name}") 

def search_tavily(query: Annotated[str, "Query to search on the web"]):
    
    """
    Searches the web using the Tavily API.

    Args:
        query (str): The search query to be used for the web search.

    Returns:
        str: A JSON-formatted string containing the search results.

    Example:
        >>> search_tavily("latest trends in AI")
        '{
            "results": [
                {"title": "AI Trends 2024", "link": "https://example.com/trends2024"},
                {"title": "The Future of AI", "link": "https://example.com/futureofai"}
            ]
        }'
    """
    
    client = TavilyClient(api_key=TAVILY_API_KEY)
    response = client.search(query, search_depth="advanced")["results"]
    df_response=pd.DataFrame(response).drop(['score','raw_content'],axis=1)
    
    return df_response.to_markdown()
