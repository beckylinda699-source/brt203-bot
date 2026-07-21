import os
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))  # your Telegram user ID
SUBSCRIBERS_FILE = "subscribers.json"

def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_subscribers(data):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(data, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    subs = load_subscribers()

    # referral tracking: /start ref_12345
    ref_id = None
    if context.args:
        ref_id = context.args[0].replace("ref_", "")

    if str(user.id) not in subs:
        subs[str(user.id)] = {
            "username": user.username,
            "referred_by": ref_id
        }
        save_subscribers(subs)

    await update.message.reply_text(
        f"Welcome {user.first_name}! You're subscribed to updates.\n\n"
        f"Your referral link:\nhttps://t.me/BRT203bot?start=ref_{user.id}"
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast your message here")
        return

    message = " ".join(context.args)
    subs = load_subscribers()
    sent, failed = 0, 0

    for uid in subs:
        try:
            await context.bot.send_message(chat_id=int(uid), text=message)
            sent += 1
        except Exception as e:
            logger.warning(f"Failed to send to {uid}: {e}")
            failed += 1

    await update.message.reply_text(f"Broadcast done. Sent: {sent}, Failed: {failed}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    subs = load_subscribers()
    await update.message.reply_text(f"Total subscribers: {len(subs)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))
    app.run_polling()

if __name__ == "__main__":
    main()
