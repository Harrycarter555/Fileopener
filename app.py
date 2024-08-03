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

if not TELEGRAM_TOKEN or not WEBHOOK_URL or not URL_SHORTENER_API_KEY or not FILE_OPENER_BOT_USERNAME:
    raise ValueError("One or more environment variables are not set.")

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for detailed logs

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
        logging.error(f"Unexpected response format: {response_data}")
        return long_url
    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        return long_url

# Function to encode URL and filename
def encode_url_and_filename(url: str, filename: str) -> str:
    combined_str = f"{url}&&{filename}"
    encoded_bytes = base64.urlsafe_b64encode(combined_str.encode('utf-8'))
    return encoded_bytes.decode('utf-8').rstrip("=")

# Function to decode URL and filename
def decode_url_and_filename(encoded_str: str) -> tuple:
    try:
        logging.debug(f"Encoded string received: {encoded_str}")

        # Ensure proper padding
        padded_encoded_str = encoded_str + '=' * (-len(encoded_str) % 4)
        logging.debug(f"Padded encoded string: {padded_encoded_str}")

        decoded_bytes = base64.urlsafe_b64decode(padded_encoded_str)
        decoded_str = decoded_bytes.decode('utf-8')
        logging.debug(f"Decoded string: {decoded_str}")

        parts = decoded_str.split('&&', 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            logging.error(f"Decoding parts issue, parts found: {parts}")
            return "", ""
    except (base64.binascii.Error, UnicodeDecodeError) as e:
        logging.error(f"Base64 decoding or Unicode decoding error: {e}")
        return "", ""
    except Exception as e:
        logging.error(f"Unexpected error during decoding: {e}")
        return "", ""

# Function to escape MarkdownV2 characters
def escape_markdown_v2(text: str) -> str:
    replacements = {
        '_': r'\_', '*': r'\*', '[': r'\[', ']': r'\]', '(': r'\(', ')': r'\)', '~': r'\~', '`': r'\`',
        '>': r'\>', '#': r'\#', '+': r'\+', '-': r'\-', '=': r'\=', '|': r'\|', '{': r'\{', '}': r'\}',
        '.': r'\.', '!': r'\!'
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text

# Handle the start command
def start(update: Update, context: CallbackContext):
    try:
        if len(context.args) == 1:
            encoded_str = context.args[0]
            logging.info(f"Received encoded string: {encoded_str}")

            decoded_url, file_name = decode_url_and_filename(encoded_str)
            if not decoded_url:
                update.message.reply_text('Error decoding the encoded string.')
                return

            logging.info(f"Decoded URL: {decoded_url}")
            logging.info(f"File Name: {file_name}")

            # Shorten the URL
            shortened_link = shorten_url(decoded_url)
            logging.info(f"Shortened URL: {shortened_link}")

            # Define photo URL
            photo_url = 'https://raw.githubusercontent.com/Harrycarter555/Fileopener/main/IMG_20240801_223423_661.jpg'

            # Prepare the message with InlineKeyboardMarkup
            keyboard = [
                [InlineKeyboardButton("🔗 Link is here", url=shortened_link)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Escape file name for MarkdownV2
            escaped_file_name = escape_markdown_v2(file_name)

            # Send the photo and message with inline keyboard
            bot.send_photo(
                chat_id=update.message.chat_id,
                photo=photo_url,
                caption=f'📸 *File Name:* {escaped_file_name}',
                parse_mode='MarkdownV2',
                reply_markup=reply_markup
            )
        else:
            logging.warning(f"Incorrect number of arguments: {context.args}")
            update.message.reply_text('Please provide the encoded URL and file name in the command.')
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

# Test encoding and decoding functions
def test_encoding_decoding():
    test_url = 'http://example.com'
    test_filename = 'myfile.txt'
    
    encoded = encode_url_and_filename(test_url, test_filename)
    print(f"Encoded: {encoded}")

    decoded_url, decoded_filename = decode_url_and_filename(encoded)
    print(f"Decoded URL: {decoded_url}")
    print(f"Decoded Filename: {decoded_filename}")

if __name__ == '__main__':
    test_encoding_decoding()
    app.run(port=5000)
