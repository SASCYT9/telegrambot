import os
import random
import requests
import spacy
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime
import pytz
from pytz import timezone
import telebot
from telebot import types
import openai
openai.api_key = "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"

# Initialize bot and API key
API_KEY = os.environ.get('API_KEY')
bot = telebot.TeleBot(API_KEY)

# Initialize NLP tools
nlp = spacy.load("en_core_web_sm")
analyzer = SentimentIntensityAnalyzer()

# Initialize markup for keyboard
markup = types.ReplyKeyboardMarkup()
markup.row('/weather', '/setreminder')
markup.row('/help')

# Define handler for /start command
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Hello! I'm your personal chatbot. How can I assist you?", reply_markup=markup)

# Define handler for /help command
@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, "Here are some commands you can use:\n/weather [city]: Get current weather information for a city.\n/setreminder [time]: Set a reminder for a specific time.", reply_markup=markup)

# Define handler for /restart command
@bot.message_handler(commands=['restart'])
def restart(message):
    bot.reply_to(message, "Bot has been restarted.", reply_markup=markup)

# Define handler for /weather command
@bot.message_handler(commands=['weather'])
def weather(message):
    city = message.text.split()[1]
    weather_api_key = os.environ.get('WEATHER_API_KEY')
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric'
    response = requests.get(url)
    data = response.json()
    if data['cod'] == 200:
        description = data['weather'][0]['description']
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        bot.reply_to(message, f"The weather in {city} is {description} with a temperature of {temp}°C, humidity of {humidity}% and wind speed of {wind_speed} m/s.", reply_markup=markup)
    else:
        bot.reply_to(message, "Sorry, I could not find weather information for that city.", reply_markup=markup)

# Define handler for /setreminder command
@bot.message_handler(commands=['setreminder'])
def setreminder(message):
    try:
        time = message.text.split()[1]
        timezone_name = 'US/Eastern'
        timezone_obj = timezone(timezone_name)
        time_obj = datetime.strptime(time, '%Y-%m-%d-%H:%M').replace(tzinfo=pytz.utc).astimezone(timezone_obj)
        time_str = time_obj.strftime('%Y-%m-%d %H:%M:%S %Z%z')
        bot.reply_to(message, f"Reminder set for {time_str}.", reply_markup=markup)
    except:
        bot.reply_to(message, "Sorry, I could not understand the time format. Please use the format: YYYY-MM-DD-HH:MM (UTC).", reply_markup=markup)

# Define handler for all other messages
# Define handler for all other messages
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    # Perform sentiment analysis
    blob = TextBlob(message.text)
    polarity = blob.sentiment.polarity
    vs = analyzer.polarity_scores(message.text)
    compound = vs['compound']
    
    # Identify named entities in message using spa
    doc = nlp(message.text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    
    # Check for weather command
    if message.text.lower().startswith('/weather'):
        # Extract city name from message
        city = message.text.lower().split()[1]
        
        # Make API request to OpenWeatherMap
        url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OWM_API_KEY}&units=metric'
        response = requests.get(url)
        data = response.json()
        
        # Parse response to extract relevant information
        weather_description = data['weather'][0]['description']
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        
        # Construct response message
        response_message = f"Current weather in {city.capitalize()}: {weather_description}. Temperature: {temp}°C (feels like {feels_like}°C). Humidity: {humidity}%."
        
    # Check for setreminder command
    elif message.text.lower().startswith('/setreminder'):
        # Extract time from message
        time = message.text.lower().split()[1]
        
        # Construct reminder message
        response_message = f"Reminder set for {time}."
        
    # Check for greeting
    elif polarity > 0:
        response_message = "Hello! How can I assist you today?"
        
    # Check for farewell
    elif polarity < 0:
        response_message = "Goodbye! Have a nice day."
        
    # Check for named entities
    elif entities:
        response_message = f"Can you tell me more about {entities[0][0]}?"
        
    # Default response
    else:
        # Generate text using OpenAI
        prompt = message.text
        response = openai.Completion.create(
            engine="text-davinci-004",
            prompt=prompt,
            max_tokens=2048,
            n=1,
            stop=None,
            temperature=0.1,
        )
        response_message = response.choices[0].text.strip()
        
    # Send response
    bot.reply_to(message, response_message, reply_markup=markup)