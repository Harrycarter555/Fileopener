import os
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
from urllib.parse import unquote
import logging

app = Flask(__name__)

# Load configuration from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
URL_SHORTENER_API_KEY = os.getenv('URL_SHORTENER_API_KEY')
CHANNEL_ID = os.getenv('CHANNEL_ID')
FILE_OPENER_BOT_USERNAME = os.getenv('FILE_OPENER_BOT_USERNAME')

if not TELEGRAM_TOKEN or not WEBHOOK_URL or not URL_SHORTENER_API_KEY or not CHANNEL_ID or not FILE_OPENER_BOT_USERNAME:
    raise ValueError("One or more environment variables are not set.")

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to shorten URL
def shorten_url(long_url: str) -> str:
    try:
        response = requests.post(
            'https://publicearn.com/api?api=d15e1e3029f8e793ad6d02cf3343365ac15ad144&url=yourdestinationlink.com&alias=CustomAlias&format=text',  # Replace with your URL shortener API endpoint
            headers={'Authorization': f'Bearer {URL_SHORTENER_API_KEY}'},
            json={'long_url': long_url}
        )
        response_data = response.json()
        if response_data.get('short_url'):
            return response_data['short_url']
        else:
            logging.error(f"Error shortening URL: {response_data}")
            return long_url  # Return original URL if shortening fails
    except Exception as e:
        logging.error(f"Exception occurred while shortening URL: {e}")
        return long_url  # Return original URL if there's an exception

# Handle the start command
def start(update: Update, context: CallbackContext):
    try:
        # Extract the start parameter if present
        if context.args:
            encoded_url = context.args[0]
            long_url = unquote(encoded_url)
            shortened_link = shorten_url(long_url)
            logging.info(f"Received URL: {long_url}")
            show_file_info(update, shortened_link)
        else:
            update.message.reply_text('Welcome! Please use the link provided in the channel.')
    except Exception as e:
        logging.error(f"Error handling /start command: {e}")
        update.message.reply_text('An error occurred. Please try again later.')

# Show file information
def show_file_info(update: Update, shorten_url: str):
    try:
        # Example data
        directory_photo = "https://example.com/directory_photo.jpg"
        file_name = "Example File"
        how_to_open_video_link = "https://example.com/how_to_open_video"

        # Format message with embedded URL
        message = (
            f'<a href="{directory_photo}">&#8205;</a>\n'
            f'File Name: {file_name}\n'
            f'Link is here: <a href="{shorten_url}">Click here</a>\n'
            f'How to Open Video: <a href="{how_to_open_video_link}">Click here</a>'
        )

        update.message.reply_text(message, parse_mode='HTML')
    except Exception as e:
        logging.error(f"Error sending file info: {e}")
        update.message.reply_text('An error occurred. Please try again later.')

# Add handlers to dispatcher
dispatcher.add_handler(CommandHandler('start', start))

# Webhook route
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok', 200

# Home route
@app.route('/')
def home():
    return 'Hello, World!'

# Webhook setup route
@app.route('/setwebhook', methods=['GET', 'POST'])
def setup_webhook():
    response = requests.post(
        f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook',
        data={'url': WEBHOOK_URL}
    )
    if response.json().get('ok'):
        return "Webhook setup ok"
    else:
        return "Webhook setup failed"

if __name__ == '__main__':
    app.run(port=5000)
