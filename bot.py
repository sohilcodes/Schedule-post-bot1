import os
import json
from datetime import datetime
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, Updater
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.error import TelegramError

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
SCHEDULE_FILE = "schedule_list.json"

bot = Bot(token=BOT_TOKEN)
scheduler = BackgroundScheduler()

# ================= SCHEDULE DATA =================
if os.path.exists(SCHEDULE_FILE):
    with open(SCHEDULE_FILE, "r") as f:
        schedule_list = json.load(f)
else:
    schedule_list = []

# ================= HELPER FUNCTIONS =================
def save_schedule():
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule_list, f, indent=2)

def get_inline_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Join Now", url="https://t.me/YourChannel")],
        [InlineKeyboardButton("💬 DM Me", url="https://t.me/YourUsername")]
    ])

def forward_public_message(channel, message_id):
    try:
        bot.forward_message(chat_id=CHANNEL_ID, from_chat_id=channel, message_id=message_id)
        print(f"Forwarded message {message_id} from {channel}")
    except TelegramError as e:
        print(f"Error forwarding {message_id} from {channel}: {e}")

def scheduled_post():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Running scheduled post at {now}")
    for item in schedule_list:
        forward_public_message(item["channel"], item["message_id"])

# ================= COMMAND HANDLERS =================
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! Use /add, /list, /remove to manage scheduled posts.")

def add(update: Update, context: CallbackContext):
    try:
        channel = context.args[0]  # @channelusername
        message_id = int(context.args[1])  # message id
        schedule_list.append({"channel": channel, "message_id": message_id})
        save_schedule()
        update.message.reply_text(f"Added to schedule: {channel} | {message_id}")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /add @ChannelUsername message_id")

def list_schedule(update: Update, context: CallbackContext):
    if not schedule_list:
        update.message.reply_text("No scheduled messages.")
        return
    msg = "\n".join([f"{i+1}. {item['channel']} | {item['message_id']}" for i, item in enumerate(schedule_list)])
    update.message.reply_text(f"Scheduled Messages:\n{msg}")

def remove(update: Update, context: CallbackContext):
    try:
        index = int(context.args[0]) - 1
        removed = schedule_list.pop(index)
        save_schedule()
        update.message.reply_text(f"Removed: {removed['channel']} | {removed['message_id']}")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /remove index_number (see /list)")

# ================= MAIN =================
def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add))
    dp.add_handler(CommandHandler("list", list_schedule))
    dp.add_handler(CommandHandler("remove", remove))

    # Schedule job
    scheduler.add_job(scheduled_post, 'cron', hour=10, minute=0)  # daily 10:00 AM
    scheduler.start()

    print("Bot running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
