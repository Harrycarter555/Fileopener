import os
import base64
import requests
from io import BytesIO
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
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

# Handle the start command
def start(update: Update, context: CallbackContext):
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

        shortened_link = shorten_url(decoded_url)
        photo_url = 'https://raw.githubusercontent.com/Harrycarter555/Fileopener/main/IMG_20240801_223423_661.jpg'
        
        # Sending a photo with a link and tutorial button
        keyboard = [
            [InlineKeyboardButton("🔗 Link is here", url=shortened_link)],
            [InlineKeyboardButton("📚 How to open (Tutorial)", url="https://example.com/tutorial")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Sending a photo with the keyboard
        bot.send_photo(
            chat_id=update.message.chat_id,
            photo=photo_url,
            caption='📸 Here is the file link:',
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

        # Stream the file
        try:
            file_response = requests.get(final_url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True)
            file_response.raise_for_status()  # Ensure we handle HTTP errors
            file_name = final_url.split('/')[-1]  # Extract file name from URL
            
            # Use BytesIO to convert file content to a file-like object
            file_content = BytesIO(file_response.content)
            
            bot.send_document(
                chat_id=update.message.chat_id,
                document=InputFile(file_content, filename=file_name),
                caption='Here is your file:',
                parse_mode='MarkdownV2'
            )
        except Exception as e:
            logging.error(f"Error streaming the file: {e}")
            update.message.reply_text(f'An error occurred while trying to stream the file: {e}')
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
