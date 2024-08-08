import os
import base64
import requests
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
import logging
import time

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

# Function to decode URL
def decode_url(encoded_str: str) -> str:
    try:
        padded_encoded_str = encoded_str + '=' * (-len(encoded_str) % 4)
        decoded_bytes = base64.urlsafe_b64decode(padded_encoded_str)
        return decoded_bytes.decode('utf-8')
    except (base64.binascii.Error, UnicodeDecodeError) as e:
        logging.error(f"Error decoding the string: {e}")
        return ""

# Function to get final URL by following redirects
def get_final_url(url: str, max_redirects: int = 10) -> str:
    """Trace the final URL after following redirects."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, allow_redirects=False, stream=True)
        redirect_count = 0
        
        while response.is_redirect and redirect_count < max_redirects:
            redirect_count += 1
            redirect_url = response.headers.get('Location')
            if redirect_url:
                response = requests.get(redirect_url, headers=headers, allow_redirects=False, stream=True)
            else:
                break
        
        return response.url
    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        return ""

# Function to download and stream the file
def download_and_stream_file(url: str, max_retries: int = 5, delay: int = 10):
    """Download and stream the file, retrying if necessary."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, stream=True)
            if response.status_code == 200:
                file_name = url.split('/')[-1]
                return InputFile(response.raw, filename=file_name)
            else:
                logging.warning(f"Retrying download, attempt {attempt + 1}/{max_retries}")
                time.sleep(delay)
        except requests.RequestException as e:
            logging.error(f"Error downloading file: {e}")
            time.sleep(delay)
    return None

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
        
        # Send a photo with a link and tutorial button
        keyboard = [
            [InlineKeyboardButton("🔗 Download File", url=shortened_link)],
            [InlineKeyboardButton("📚 How to open (Tutorial)", url="https://example.com/tutorial")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send a photo with the keyboard
        bot.send_photo(
            chat_id=update.message.chat_id,
            photo=photo_url,
            caption='📸 Here is the file link:',
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

    else:
        update.message.reply_text('Please provide the encoded URL in the command.')

# Handle the file streaming command
def stream_file(update: Update, context: CallbackContext):
    if len(context.args) == 1:
        encoded_str = context.args[0]
        decoded_url = decode_url(encoded_str)
        if not decoded_url:
            update.message.reply_text('Error decoding the encoded string.')
            return

        final_url = get_final_url(decoded_url)
        if not final_url:
            update.message.reply_text('Error fetching the final URL.')
            return

        file_input = download_and_stream_file(final_url)
        if file_input:
            try:
                bot.send_document(
                    chat_id=update.message.chat_id,
                    document=file_input,
                    caption='Here is your file:',
                    parse_mode='MarkdownV2'
                )
            except Exception as e:
                logging.error(f"Error streaming the file: {e}")
                update.message.reply_text(f'An error occurred while trying to stream the file: {e}')
        else:
            update.message.reply_text('Failed to download the file after multiple attempts.')
    else:
        update.message.reply_text('Please provide the encoded URL in the command.')

# Add handlers to dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('stream', stream_file))

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
