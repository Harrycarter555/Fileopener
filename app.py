import os
import base64
import requests
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
import logging

app = Flask(__name__)

# Load configuration from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
URL_SHORTENER_API_KEY = os.getenv('URL_SHORTENER_API_KEY')
FILE_OPENER_BOT_USERNAME = os.getenv('FILE_OPENER_BOT_USERNAME')

# Validate environment variables
if not TELEGRAM_TOKEN or not WEBHOOK_URL or not URL_SHORTENER_API_KEY or not FILE_OPENER_BOT_USERNAME:
    raise ValueError("One or more environment variables are not set.")

# Initialize Telegram bot and dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Function to shorten URL
def shorten_url(long_url: str) -> str:
    encoded_url = requests.utils.quote(long_url)
    api_url = f"https://publicearn.com/api?api={URL_SHORTENER_API_KEY}&url={encoded_url}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        response_data = response.json()
        if response_data.get("status") == "success":
            return response_data.get("shortenedUrl", long_url)
    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
    return long_url

# Function to encode URL
def encode_url(url: str) -> str:
    encoded_bytes = base64.urlsafe_b64encode(url.encode('utf-8'))
    return encoded_bytes.decode('utf-8').rstrip("=")

# Function to decode URL
def decode_url(encoded_str: str) -> str:
    try:
        padded_encoded_str = encoded_str + '=' * (-len(encoded_str) % 4)
        decoded_bytes = base64.urlsafe_b64decode(padded_encoded_str)
        return decoded_bytes.decode('utf-8')
    except (base64.binascii.Error, UnicodeDecodeError) as e:
        logging.error(f"Error decoding the string: {e}")
        return ""

# Handle the start command
def start(update: Update, context: CallbackContext):
    if len(context.args) == 1:
        encoded_str = context.args[0]
        decoded_url = decode_url(encoded_str)
        if not decoded_url:
            update.message.reply_text('Error decoding the encoded string.')
            return

        shortened_link = shorten_url(decoded_url)
        photo_url = 'https://raw.githubusercontent.com/Harrycarter555/Fileopener/main/IMG_20240801_223423_661.jpg'

        keyboard = [
            [InlineKeyboardButton("🔗 Link is here", url=shortened_link)],
            [InlineKeyboardButton("📚 How to open (Tutorial)", url="https://example.com/tutorial")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        bot.send_photo(
            chat_id=update.message.chat_id,
            photo=photo_url,
            caption='📸 Here is the file link:',
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
    else:
        update.message.reply_text('Please provide the encoded URL in the command.')

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
        logging.error(f"Webhook setup failed: {response.json()}")
        return "Webhook setup failed"

if __name__ == '__main__':
    app.run(port=5000)
