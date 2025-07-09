import requests
from flask import Blueprint, request, jsonify
import os
from dotenv import load_dotenv

chatbot_bp = Blueprint('chatbot', __name__)

# Load environment variables from .env file
load_dotenv()

OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
if not OPENWEATHER_API_KEY:
    raise RuntimeError("OPENWEATHER_API_KEY environment variable not set.")


def extract_location_and_intent(message):
    """
    Very basic intent and location extraction for demo purposes.
    """
    message = message.lower()
    if 'weather' in message or 'rain' in message or 'temperature' in message:
        # Try to extract a city name (very basic, for demo)
        words = message.split()
        for i, word in enumerate(words):
            if word in ['in', 'at', 'for'] and i + 1 < len(words):
                return words[i + 1], 'weather'
        # Default location if not found
        return 'Nairobi', 'weather'
    return None, None


def get_weather(city):
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric'
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        return f"It's currently {temp}°C with {desc} in {city.title()}."
    else:
        return f"Sorry, I couldn't find weather data for {city.title()}."


@chatbot_bp.route('/api/chatbot', methods=['POST'])
def chatbot():
    user_message = request.json.get('message', '')
    city, intent = extract_location_and_intent(user_message)
    if intent == 'weather':
        response = get_weather(city)
    else:
        response = "I'm a weather bot! Ask me about the weather in any city."
    return jsonify({'response': response})
