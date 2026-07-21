import os
import logging
import json
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
SUBSCRIBERS_FILE = "subscribers.json"

# Adjust this to control broadcast speed (seconds between each message)
BROADCAST_DELAY = 0.05  # ~20 messages/sec, safely under Telegram's limits


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
    uid = str(user.id)

    # referral tracking: /start ref_12345
    ref_id = None
    if context.args:
        ref_id = context.args[0].replace("ref_", "")

    if uid not in subs:
        subs[uid] = {
            "username": user.username,
            "referred_by": ref_id,
            "active": True
        }
        save_subscribers(subs)

        # credit the referrer
        if ref_id and ref_id in subs and ref_id != uid:
            subs[ref_id].setdefault("referral_count", 0)
            subs[ref_id]["referral_count"] += 1
            save_subscribers(subs)
    else:
        # user came back after having stopped — reactivate
        subs[uid]["active"] = True
        save_subscribers(subs)

    await update.message.reply_text(
        f"Welcome {user.first_name}! You're subscribed to updates.\n\n"
        f"Your referral link:\nhttps://t.me/BRT203bot?start=ref_{user.id}\n\n"
        f"Send /stop anytime to unsubscribe."
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    subs = load_subscribers()
    uid = str(user.id)

    if uid in subs:
        subs[uid]["active"] = False
        save_subscribers(subs)
        await update.message.reply_text(
            "You've been unsubscribed. Send /start anytime to rejoin."
        )
    else:
        await update.message.reply_text("You're not currently subscribed.")


async def myreferrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    subs = load_subscribers()
    uid = str(user.id)
    count = subs.get(uid, {}).get("referral_count", 0)
    await update.message.reply_text(f"You've referred {count} people so far!")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast your message here")
        return

    message = " ".join(context.args)
    subs = load_subscribers()
    active_subs = [uid for uid, data in subs.items() if data.get("active", True)]

    if not active_subs:
        await update.message.reply_text("No active subscribers to broadcast to.")
        return

    await update.message.reply_text(f"Starting broadcast to {len(active_subs)} subscribers...")

    sent, failed = 0, 0
    for uid in active_subs:
        try:
            await context.bot.send_message(chat_id=int(uid), text=message)
            sent += 1
        except Exception as e:
            logger.warning(f"Failed to send to {uid}: {e}")
            # if user blocked the bot, mark them inactive
            if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                subs[uid]["active"] = False
            failed += 1
        await asyncio.sleep(BROADCAST_DELAY)

    save_subscribers(subs)
    await update.message.reply_text(f"Broadcast done. Sent: {sent}, Failed: {failed}")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    subs = load_subscribers()
    total = len(subs)
    active = sum(1 for d in subs.values() if d.get("active", True))
    await update.message.reply_text(
        f"Total subscribers: {total}\nActive: {active}\nUnsubscribed: {total - active}"
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("myreferrals", myreferrals))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))
    app.run_polling()


if __name__ == "__main__":
    main()
