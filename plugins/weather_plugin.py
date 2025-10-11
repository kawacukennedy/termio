"""
Weather Plugin for Auralis
Provides weather information and forecasts
"""

import requests
import json
from datetime import datetime

def register_plugin():
    """Register this plugin with Auralis"""
    return {
        "name": "weather",
        "version": "1.0.0",
        "description": "Get weather information and forecasts",
        "commands": ["get_weather", "forecast", "weather_alerts"]
    }

def get_weather(city="New York", api_key=None):
    """Get current weather for a city"""
    if not api_key:
        return "Weather API key required. Configure with 'store api key openweather YOUR_KEY'"

    try:
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': api_key,
            'units': 'metric'
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code == 200:
            weather = data['weather'][0]['description'].title()
            temp = data['main']['temp']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']

            return f"Weather in {city}: {weather}, {temp}°C, Humidity: {humidity}%, Wind: {wind_speed} m/s"
        else:
            return f"Weather error: {data.get('message', 'Unknown error')}"

    except Exception as e:
        return f"Weather service error: {e}"

def forecast(city="New York", days=3, api_key=None):
    """Get weather forecast for a city"""
    if not api_key:
        return "Weather API key required"

    try:
        url = "http://api.openweathermap.org/data/2.5/forecast"
        params = {
            'q': city,
            'appid': api_key,
            'units': 'metric'
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code == 200:
            forecast_list = data['list'][:days*8]  # 8 entries per day (3-hour intervals)

            forecast_text = f"{days}-day forecast for {city}:\n"
            current_day = None

            for entry in forecast_list:
                dt = datetime.fromtimestamp(entry['dt'])
                day = dt.strftime('%A')

                if day != current_day:
                    current_day = day
                    weather = entry['weather'][0]['description'].title()
                    temp_min = entry['main']['temp_min']
                    temp_max = entry['main']['temp_max']
                    forecast_text += f"{day}: {weather}, {temp_min}°C - {temp_max}°C\n"

            return forecast_text
        else:
            return f"Forecast error: {data.get('message', 'Unknown error')}"

    except Exception as e:
        return f"Forecast service error: {e}"

def weather_alerts(location="US", api_key=None):
    """Get weather alerts for a location"""
    # This would require a different API endpoint
    # For demonstration, return a placeholder
    return f"Weather alerts for {location}: No active alerts (demo feature)"