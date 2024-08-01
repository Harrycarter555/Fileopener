import os
import requests
from flask import Flask, request, send_from_directory
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext

app = Flask(__name__)

# Load configuration from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

if not TELEGRAM_TOKEN or not WEBHOOK_URL:
    raise ValueError("TELEGRAM_TOKEN and WEBHOOK_URL environment variables are not set.")

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Define the start command handler
def start(update: Update, context: CallbackContext):
    # Extract the shorten_url from the command argument
    if context.args:
        shorten_url = context.args[0]
        
        # Example data (You will replace these with actual data)
        directory_photo = "https://example.com/photo.jpg"
        file_name = "Sample File Name"
        tutorial_link = "https://example.com/tutorial"

        # Message formatting
        message = (
            f"Directory Photo: {directory_photo}\n\n"
            f"File Name: {file_name}\n"
            f"Link is Here: {shorten_url}\n"
            f"How to Open Video: {tutorial_link}"
        )
        
        # Send the message to the user with the photo and caption
        update.message.reply_photo(photo=directory_photo, caption=message)
        
        # Implement URL shortener tracking and streaming logic here
    else:
        update.message.reply_text("Invalid link provided.")

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

# Favicon route
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.getcwd(), 'favicon.ico')

# Webhook setup route
@app.route('/setwebhook', methods=['GET', 'POST'])
def setup_webhook():
    webhook_url = f'{WEBHOOK_URL}'  # Ensure this URL is correct
    response = requests.post(
        f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook',
        data={'url': webhook_url}
    )
    if response.json().get('ok'):
        return "Webhook setup ok"
    else:
        return "Webhook setup failed"

if __name__ == '__main__':
    app.run(port=5000)
