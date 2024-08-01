import os
import requests
from flask import Flask, request, send_from_directory
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext

app = Flask(__name__)

# Load configuration from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
FILE_OPENER_BOT_USERNAME = os.getenv('FILE_OPENER_BOT_USERNAME')

if not TELEGRAM_TOKEN or not WEBHOOK_URL or not FILE_OPENER_BOT_USERNAME:
    raise ValueError("One or more environment variables are not set.")

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Define the start command handler
def start(update: Update, context: CallbackContext):
    if context.args:
        shortened_url = context.args[0]  # Extract shortened URL from command argument
        
        # Example details
        file_name = "Sample File Name"  # Replace with actual file name fetching logic
        how_to_open_video_link = "http://tutorial.example.com"  # Replace with actual tutorial link
        
        # Example photo URL (same for all files)
        PHOTO_URL = 'https://example.com/path/to/photo.jpg'
        
        # Create a message with the file details
        message = (
            f"File Name: {file_name}\n\n"
            f"Link is Here:\n{shortened_url}\n\n"
            f"How to Open Video:\n{how_to_open_video_link}"
        )
        
        # Send the photo and message to the user
        bot.send_photo(chat_id=update.message.chat_id, photo=PHOTO_URL, caption=message)
        print(f"Sent photo and message to user: {update.message.chat_id}")
    else:
        update.message.reply_text('Invalid link. Please use the correct link provided in the channel.')
        print(f"Invalid link received: {context.args}")

# Add handlers to dispatcher
dispatcher.add_handler(CommandHandler('start', start))

# Webhook route
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        print(f"Update processed: {update}")
        return 'ok', 200
    except Exception as e:
        print(f'Error processing update: {e}')
        return 'error', 500

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
