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
def shorten_url(long_url: str, file_name: str) -> str:
    api_token = URL_SHORTENER_API_KEY
    encoded_url = requests.utils.quote(long_url)
    encoded_file_name = requests.utils.quote(file_name)
    api_url = f"https://publicearn.com/api?api={api_token}&url={encoded_url}||{encoded_file_name}"

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
        encoded_url, encoded_file_name = encoded_params.split('||')
        decoded_url = base64.urlsafe_b64decode(encoded_url + '==').decode()
        decoded_file_name = base64.urlsafe_b64decode(encoded_file_name + '==').decode()
        return decoded_url, decoded_file_name
    except Exception as e:
        logging.error(f"Error decoding parameters: {e}")
        raise ValueError("Invalid parameters")

# Handle the start command
def start(update: Update, context: CallbackContext):
    try:
        query = update.message.text
        if query.startswith("/start"):
            encoded_params = query[len("/start "):]  # Get parameters after /start

            if encoded_params:
                try:
                    decoded_url, file_name = decode_start_params(encoded_params)
                except ValueError:
                    update.message.reply_text('Error decoding parameters.')
                    return

                logging.info(f"Decoded URL: {decoded_url}")
                logging.info(f"File Name: {file_name}")

                shortened_link = shorten_url(decoded_url, file_name)
                logging.info(f"Shortened URL: {shortened_link}")

                photo_url = 'https://github.com/Harrycarter555/Fileopener/blob/main/IMG_20240801_223423_661.jpg'
                tutorial_link = 'https://example.com/tutorial'

                message = (f'📸 *File Name:* {file_name}\n\n'
                           f'🔗 *Link is Here:* [Here]({shortened_link})\n\n'
                           f'📘 *How to open Tutorial:* [Tutorial]({tutorial_link})')

                bot.send_photo(chat_id=update.message.chat_id, photo=photo_url)
                update.message.reply_text(message, parse_mode='MarkdownV2')
            else:
                update.message.reply_text('Please provide the encoded parameters in the command.')
        else:
            update.message.reply_text('Invalid command format. Please use the correct format.')
    except Exception as e:
        logging.error(f"Error handling /start command: {e}")
        update.message.reply_text('An error occurred. Please try again later.')

# Generate file opener URL
def generate_file_opener_url(long_url: str, file_name: str) -> str:
    encoded_params = encode_start_params(long_url, file_name)
    file_opener_url = f'https://t.me/{FILE_OPENER_BOT_USERNAME}?start={encoded_params}'
    return file_opener_url

# Example usage
long_url = "https://publicearn.com/somefile"
file_name = "example.txt"
print("File Opener URL:", generate_file_opener_url(long_url, file_name))

# Add handlers to dispatcher
dispatcher.add_handler(CommandHandler('start', start))

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
    app.run(port=5000, threaded=True)
