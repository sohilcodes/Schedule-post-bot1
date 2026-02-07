import os
import json
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.error import TelegramError

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
SCHEDULE_FILE = "schedule_list.json"

# ================= LOAD SCHEDULE DATA =================
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

async def forward_public_message(channel, message_id, application):
    try:
        await application.bot.forward_message(chat_id=CHANNEL_ID, from_chat_id=channel, message_id=message_id)
        print(f"Forwarded message {message_id} from {channel}")
    except TelegramError as e:
        print(f"Error forwarding {message_id} from {channel}: {e}")

def scheduled_post(application):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Running scheduled post at {now}")
    for item in schedule_list:
        application.create_task(forward_public_message(item["channel"], item["message_id"], application))

# ================= COMMAND HANDLERS =================
async def start(update, context):
    await update.message.reply_text("Welcome! Use /add, /list, /remove to manage scheduled posts.")

async def add(update, context):
    try:
        channel = context.args[0]  # @channelusername
        message_id = int(context.args[1])  # message id
        schedule_list.append({"channel": channel, "message_id": message_id})
        save_schedule()
        await update.message.reply_text(f"Added to schedule: {channel} | {message_id}")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /add @ChannelUsername message_id")

async def list_schedule(update, context):
    if not schedule_list:
        await update.message.reply_text("No scheduled messages.")
        return
    msg = "\n".join([f"{i+1}. {item['channel']} | {item['message_id']}" for i, item in enumerate(schedule_list)])
    await update.message.reply_text(f"Scheduled Messages:\n{msg}")

async def remove(update, context):
    try:
        index = int(context.args[0]) - 1
        removed = schedule_list.pop(index)
        save_schedule()
        await update.message.reply_text(f"Removed: {removed['channel']} | {removed['message_id']}")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /remove index_number (see /list)")

# ================= MAIN =================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_schedule))
    app.add_handler(CommandHandler("remove", remove))

    # Scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: scheduled_post(app), 'cron', hour=10, minute=0)  # daily 10:00 AM
    scheduler.start()

    print("Bot running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
