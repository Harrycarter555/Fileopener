import os
import requests
from flask import Flask, request
from telegram import Bot, Update, InputMediaPhoto
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, CallbackQueryHandler

app = Flask(__name__)

# Load configuration from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
CHANNEL_ID = os.getenv('CHANNEL_ID')
FILE_OPENER_BOT_USERNAME = os.getenv('FILE_OPENER_BOT_USERNAME')

if not TELEGRAM_TOKEN or not WEBHOOK_URL or not CHANNEL_ID or not FILE_OPENER_BOT_USERNAME:
    raise ValueError("One or more environment variables are not set.")

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

def start(update: Update, context: CallbackContext):
    # Extract the shorten_url from the command argument
    query = update.message.text.split(" ")[1] if len(update.message.text.split(" ")) > 1 else None
    if query:
        # Example data for demonstration
        directory_photo = "https://example.com/photo.jpg"
        file_name = "Sample File Name"
        tutorial_link = "https://example.com/tutorial"

        message = (
            f"Directory Photo: {directory_photo}\n\n"
            f"File Name: {file_name}\n"
            f"Link is Here: {query}\n"
            f"How to Open Video: {tutorial_link}"
        )
        
        # Send the message to the user
        update.message.reply_photo(photo=directory_photo, caption=message)
        
        # Optionally, you can also handle URL shortener tracking here
        # and eventually provide the streaming URL
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
