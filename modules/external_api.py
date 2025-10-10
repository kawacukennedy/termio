import requests
import json
from datetime import datetime
import os

class ExternalAPIModule:
    def __init__(self, config, security_module):
        self.config = config
        self.security = security_module
        self.api_endpoints = {
            'weather': 'http://api.openweathermap.org/data/2.5/weather',
            'news': 'https://newsapi.org/v2/top-headlines',
            'joke': 'https://official-joke-api.appspot.com/random_joke',
            'quote': 'https://api.quotable.io/random',
            'time': 'http://worldtimeapi.org/api/ip',
            'currency': 'https://api.exchangerate-api.com/v4/latest/USD'
        }

    def get_weather(self, city='New York'):
        """Get weather information for a city"""
        api_key = self.security.get_api_key('openweather')
        if not api_key:
            return "OpenWeather API key not configured. Use 'store api key openweather YOUR_KEY'"

        try:
            params = {
                'q': city,
                'appid': api_key,
                'units': 'metric'
            }
            response = requests.get(self.api_endpoints['weather'], params=params, timeout=10)
            data = response.json()

            if response.status_code == 200:
                weather = data['weather'][0]['description']
                temp = data['main']['temp']
                humidity = data['main']['humidity']
                return f"Weather in {city}: {weather}, {temp}°C, humidity {humidity}%"
            else:
                return f"Weather API error: {data.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Weather service unavailable: {e}"

    def get_news(self, category='technology', country='us'):
        """Get top news headlines"""
        api_key = self.security.get_api_key('newsapi')
        if not api_key:
            return "NewsAPI key not configured. Use 'store api key newsapi YOUR_KEY'"

        try:
            params = {
                'apiKey': api_key,
                'country': country,
                'category': category,
                'pageSize': 3
            }
            response = requests.get(self.api_endpoints['news'], params=params, timeout=10)
            data = response.json()

            if response.status_code == 200:
                articles = data.get('articles', [])
                if not articles:
                    return f"No {category} news found for {country}"

                headlines = []
                for article in articles[:3]:
                    title = article.get('title', 'No title')
                    source = article.get('source', {}).get('name', 'Unknown')
                    headlines.append(f"• {title} ({source})")

                return f"Top {category} news:\n" + "\n".join(headlines)
            else:
                return f"News API error: {data.get('message', 'Unknown error')}"
        except Exception as e:
            return f"News service unavailable: {e}"

    def get_joke(self):
        """Get a random joke"""
        try:
            response = requests.get(self.api_endpoints['joke'], timeout=5)
            data = response.json()

            if response.status_code == 200:
                setup = data.get('setup', '')
                punchline = data.get('punchline', '')
                return f"{setup}\n{punchline}"
            else:
                return "Couldn't fetch a joke right now"
        except Exception as e:
            return f"Joke service unavailable: {e}"

    def get_quote(self):
        """Get an inspirational quote"""
        try:
            response = requests.get(self.api_endpoints['quote'], timeout=5)
            data = response.json()

            if response.status_code == 200:
                quote = data.get('content', '')
                author = data.get('author', 'Unknown')
                return f'"{quote}"\n— {author}'
            else:
                return "Couldn't fetch a quote right now"
        except Exception as e:
            return f"Quote service unavailable: {e}"

    def get_time(self, timezone=None):
        """Get current time for timezone or IP location"""
        try:
            url = f"{self.api_endpoints['time']}/{timezone}" if timezone else self.api_endpoints['time']
            response = requests.get(url, timeout=5)
            data = response.json()

            if response.status_code == 200:
                datetime_str = data.get('datetime', '')
                timezone_name = data.get('timezone', 'Unknown')
                if datetime_str:
                    # Parse and format
                    dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                    return f"Current time in {timezone_name}: {dt.strftime('%Y-%m-%d %H:%M:%S')}"
                else:
                    return f"Time data unavailable for {timezone_name}"
            else:
                return "Time service error"
        except Exception as e:
            return f"Time service unavailable: {e}"

    def get_currency_rate(self, from_currency='USD', to_currency='EUR'):
        """Get currency exchange rate"""
        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
            response = requests.get(url, timeout=5)
            data = response.json()

            if response.status_code == 200:
                rates = data.get('rates', {})
                if to_currency in rates:
                    rate = rates[to_currency]
                    return f"1 {from_currency} = {rate} {to_currency}"
                else:
                    return f"Currency {to_currency} not found"
            else:
                return "Currency service error"
        except Exception as e:
            return f"Currency service unavailable: {e}"

    def search_wikipedia(self, query):
        """Search Wikipedia for information"""
        try:
            # Using Wikipedia API
            params = {
                'action': 'query',
                'format': 'json',
                'prop': 'extracts',
                'exintro': True,
                'explaintext': True,
                'titles': query
            }
            response = requests.get('https://en.wikipedia.org/api/rest_v1/page/summary/' + query.replace(' ', '_'), timeout=10)

            if response.status_code == 200:
                data = response.json()
                title = data.get('title', query)
                extract = data.get('extract', '')

                if extract:
                    # Truncate to first 500 characters
                    summary = extract[:500] + '...' if len(extract) > 500 else extract
                    return f"Wikipedia: {title}\n{summary}"
                else:
                    return f"No Wikipedia page found for '{query}'"
            else:
                return f"Wikipedia search failed for '{query}'"
        except Exception as e:
            return f"Wikipedia service unavailable: {e}"

    def get_available_services(self):
        """List available external services"""
        services = {
            'weather': 'Get weather for any city (requires OpenWeather API key)',
            'news': 'Get top news headlines (requires NewsAPI key)',
            'joke': 'Get a random joke',
            'quote': 'Get an inspirational quote',
            'time': 'Get current time for any timezone',
            'currency': 'Get currency exchange rates',
            'wikipedia': 'Search Wikipedia for information'
        }
        return services