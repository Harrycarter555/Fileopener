import os
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
from urllib.parse import unquote

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

# Handle the start command
def start(update: Update, context: CallbackContext):
    if context.args:
        encoded_url = context.args[0]
        print(f"Received encoded URL: {encoded_url}")
        shorten_url = unquote(encoded_url)
        print(f"Decoded URL: {shorten_url}")
        show_file_info(update, shorten_url)
    else:
        update.message.reply_text('Welcome! Please use the link provided in the channel.')

# Show file information
def show_file_info(update: Update, shorten_url: str):
    directory_photo = "https://example.com/directory_photo.jpg"
    file_name = "Example File"
    how_to_open_video_link = "https://example.com/how_to_open_video"

    message = (
        f'<a href="{directory_photo}">&#8205;</a>\n'
        f'File Name: {file_name}\n'
        f'Link is here: <a href="{shorten_url}">Click here</a>\n'
        f'How to Open Video: <a href="{how_to_open_video_link}">Click here</a>'
    )

    update.message.reply_text(message, parse_mode='HTML')

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
