import os
import base64
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
import logging

app = Flask(__name__)

# Load configuration from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
URL_SHORTENER_API_KEY = os.getenv('URL_SHORTENER_API_KEY')
FILE_OPENER_BOT_USERNAME = os.getenv('FILE_OPENER_BOT_USERNAME')

if not TELEGRAM_TOKEN or not WEBHOOK_URL or not URL_SHORTENER_API_KEY or not FILE_OPENER_BOT_USERNAME:
    raise ValueError("One or more environment variables are not set.")

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to shorten URL
def shorten_url(long_url: str) -> str:
    api_token = URL_SHORTENER_API_KEY
    encoded_url = requests.utils.quote(long_url)
    api_url = f"https://publicearn.com/api?api={api_token}&url={encoded_url}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        
        response_data = response.json()
        if response_data.get("status") == "success":
            short_url = response_data.get("shortenedUrl", "")
            if short_url:
                return short_url
        logging.error("Unexpected response format or empty shortened URL")
        return long_url
    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        return long_url

# Encode parameters
def encode_start_params(url: str, file_name: str) -> str:
    encoded_url = base64.urlsafe_b64encode(url.encode()).decode().rstrip('=')
    encoded_file_name = base64.urlsafe_b64encode(file_name.encode()).decode().rstrip('=')
    return f'{encoded_url}||{encoded_file_name}'

# Decode parameters
def decode_start_params(encoded_params: str) -> tuple:
    try:
        padded_encoded_params = encoded_params + '=='
        decoded_bytes = base64.urlsafe_b64decode(padded_encoded_params)
        decoded_str = decoded_bytes.decode('utf-8')
        decoded_url, decoded_file_name = decoded_str.split('||', 1)
        return decoded_url, decoded_file_name
    except Exception as e:
        logging.error(f"Error decoding parameters: {e}")
        return None, None

# Handle the start command
def start(update: Update, context: CallbackContext):
    try:
        if context.args and len(context.args) == 1:
            encoded_params = context.args[0]
            decoded_url, file_name = decode_start_params(encoded_params)
            if decoded_url and file_name:
                shortened_link = shorten_url(decoded_url)
                update.message.reply_text(f'Here is your file link: {shortened_link}\n\nFile Name: {file_name}')
            else:
                update.message.reply_text('Invalid parameters or decoding error.')
        else:
            update.message.reply_text('Please provide the encoded parameters.')
    except Exception as e:
        logging.error(f"Error handling /start command: {e}")
        update.message.reply_text('An error occurred. Please try again later.')

# Webhook route
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return 'ok', 200
    except Exception as e:
        logging.error(f'Error processing update: {e}')
        return 'error', 500

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
    app.run(port=5001, threaded=True)
