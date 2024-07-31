import os
import requests
from flask import Flask, request, send_from_directory
from telegram import Bot, Update, InputMediaPhoto
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, CallbackQueryHandler

app = Flask(__name__)

# Load configuration from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
FILE_OPENER_BOT_USERNAME = os.getenv('FILE_OPENER_BOT_USERNAME')

missing_vars = []
if not TELEGRAM_TOKEN:
    missing_vars.append('TELEGRAM_TOKEN')
if not WEBHOOK_URL:
    missing_vars.append('WEBHOOK_URL')
if not FILE_OPENER_BOT_USERNAME:
    missing_vars.append('FILE_OPENER_BOT_USERNAME')

if missing_vars:
    raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Define the start command handler
def start(update: Update, context: CallbackContext):
    # Check if there's a URL parameter in the start command
    if context.args:
        link = context.args[0]
        file_name = "Sample File Name"  # Replace with actual file name logic
        shorten_link = link  # Shorten the URL if necessary
        tutorial_link = "http://tutorial.example.com"  # Replace with actual tutorial link

        # Example photo URL (same for all files)
        PHOTO_URL = 'https://example.com/path/to/photo.jpg'

        # Create a message with the file details
        message = (
            f"File Name: {file_name}\n\n"
            f"Link is Here:\n{shorten_link}\n\n"
            f"How to Open Tutorial:\n{tutorial_link}"
        )

        # Send the photo and message to the user
        bot.send_photo(chat_id=update.message.chat_id, photo=PHOTO_URL, caption=message)
    else:
        update.message.reply_text('Welcome! Please use the link provided in the channel.')

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
