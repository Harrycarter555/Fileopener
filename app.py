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

if not TELEGRAM_TOKEN or not WEBHOOK_URL or not URL_SHORTENER_API_KEY:
    raise ValueError("One or more environment variables are not set.")

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to shorten URL
def shorten_url(long_url: str) -> str:
    api_token = URL_SHORTENER_API_KEY
    encoded_url = requests.utils.quote(long_url)  # URL encode the long URL
    api_url = f"https://publicearn.com/api?api={api_token}&url={encoded_url}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        response_data = response.json()
        if response_data.get("status") == "success":
            short_url = response_data.get("shortenedUrl", "")
            if short_url:
                return short_url
        logging.error("Unexpected response format")
        return long_url
    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        return long_url

# Handle the start command
def start(update: Update, context: CallbackContext):
    try:
        if len(context.args) == 1:
            encoded_str = context.args[0]
            
            # Decode the URL and file name
            padded_encoded_str = encoded_str + '=='  # Add padding for base64 compliance
            try:
                decoded_str = base64.urlsafe_b64decode(padded_encoded_str).decode('utf-8')
            except Exception as e:
                logging.error(f"Base64 decoding error: {e}")
                update.message.reply_text('Error decoding base64 string.')
                return
            
            logging.info(f"Decoded String: {decoded_str}")
            
            # Split into URL and file name using delimiter
            delimiter = '&&'
            if delimiter in decoded_str:
                try:
                    decoded_url, file_name = decoded_str.split(delimiter, 1)
                    logging.info(f"Decoded URL: {decoded_url}")
                    logging.info(f"File Name: {file_name}")

                    # Shorten the URL
                    shortened_link = shorten_url(decoded_url)
                    logging.info(f"Shortened URL: {shortened_link}")

                    # Define photo URL and tutorial link
                    photo_url = 'https://github.com/Harrycarter555/Fileopener/blob/main/IMG_20240801_223423_661.jpg'
                    tutorial_link = 'https://example.com/tutorial'  # Replace with actual tutorial link

                    # Prepare the message with MarkdownV2 formatting
                    message = (f'📸 *File Name:* {file_name}\n\n'
                               f'🔗 *Link is Here:* [Here]({shortened_link})\n\n'
                               f'📘 *How to open Tutorial:* [Tutorial]({tutorial_link})')

                    # Send the photo first
                    bot.send_photo(chat_id=update.message.chat_id, photo=photo_url)

                    # Send the formatted message
                    update.message.reply_text(message, parse_mode='MarkdownV2')
                except Exception as e:
                    logging.error(f"Error splitting the decoded string: {e}")
                    update.message.reply_text('Error processing the decoded string.')
            else:
                logging.warning(f"Invalid format of the encoded string: {decoded_str}")
                update.message.reply_text('Invalid format of the encoded string.')
        else:
            logging.warning(f"Missing arguments: {context.args}")
            update.message.reply_text('Please provide the encoded string in the command.')
    except Exception as e:
        logging.error(f"Error handling /start command: {e}")
        update.message.reply_text(f'An error occurred: {e}')

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
    app.run(port=5000)
