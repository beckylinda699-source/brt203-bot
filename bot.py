import os
import logging
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
DATABASE_URL = os.environ.get("DATABASE_URL")
BROADCAST_DELAY = 0.05

BOT_USERNAME = "BRT203bot"


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            referred_by BIGINT,
            referral_count INT DEFAULT 0,
            active BOOLEAN DEFAULT TRUE
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    ref_id = None
    if context.args:
        try:
            ref_id = int(context.args[0].replace("ref_", ""))
        except ValueError:
            ref_id = None

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM subscribers WHERE user_id = %s", (uid,))
    existing = cur.fetchone()

    if not existing:
        cur.execute(
            "INSERT INTO subscribers (user_id, username, referred_by, active) VALUES (%s, %s, %s, TRUE)",
            (uid, user.username, ref_id)
        )
        if ref_id and ref_id != uid:
            cur.execute(
                "UPDATE subscribers SET referral_count = referral_count + 1 WHERE user_id = %s",
                (ref_id,)
            )
    else:
        cur.execute("UPDATE subscribers SET active = TRUE WHERE user_id = %s", (uid,))

    conn.commit()
    cur.close()
    conn.close()

    await update.message.reply_text(
        f"Welcome {user.first_name}! You're subscribed to updates.\n\n"
        f"Your referral link:\nhttps://t.me/{BOT_USERNAME}?start=ref_{uid}\n\n"
        f"Send /help to see all commands, or /stop anytime to unsubscribe."
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM subscribers WHERE user_id = %s", (uid,))
    existing = cur.fetchone()

    if existing:
        cur.execute("UPDATE subscribers SET active = FALSE WHERE user_id = %s", (uid,))
        conn.commit()
        await update.message.reply_text("You've been unsubscribed. Send /start anytime to rejoin.")
    else:
        await update.message.reply_text("You're not currently subscribed.")

    cur.close()
    conn.close()


async def myreferrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT referral_count FROM subscribers WHERE user_id = %s", (uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    count = row["referral_count"] if row else 0
    await update.message.reply_text(f"You've referred {count} people so far!")


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT username, referral_count FROM subscribers "
        "WHERE referral_count > 0 ORDER BY referral_count DESC LIMIT 10"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        await update.message.reply_text("No referrals yet. Be the first!")
        return

    text = "🏆 Top Referrers\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, row in enumerate(rows):
        prefix = medals[i] if i < 3 else f"{i+1}."
        name = f"@{row['username']}" if row["username"] else "Anonymous"
        text += f"{prefix} {name} — {row['referral_count']} referrals\n"

    await update.message.reply_text(text)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Subscribe & get your referral link\n"
        "/stop - Unsubscribe from updates\n"
        "/myreferrals - See your referral count\n"
        "/leaderboard - See top referrers\n"
        "/help - Show this message"
    )


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Not authorized.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /broadcast your message here\n\n"
            "Supports HTML formatting:\n"
            "<b>bold</b>, <i>italic</i>, <a href='https://example.com'>link</a>"
        )
        return

    message = " ".join(context.args)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM subscribers WHERE active = TRUE")
    active_subs = [row["user_id"] for row in cur.fetchall()]
    cur.close()

    if not active_subs:
        await update.message.reply_text("No active subscribers to broadcast to.")
        conn.close()
        return

    await update.message.reply_text(f"Starting broadcast to {len(active_subs)} subscribers...")

    sent, failed = 0, 0
    cur = conn.cursor()
    for uid in active_subs:
        try:
            await context.bot.send_message(
                chat_id=uid, text=message, parse_mode=ParseMode.HTML
            )
            sent += 1
        except Exception as e:
            logger.warning(f"Failed to send to {uid}: {e}")
            if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                cur.execute("UPDATE subscribers SET active = FALSE WHERE user_id = %s", (uid,))
            failed += 1
        await asyncio.sleep(BROADCAST_DELAY)

    conn.commit()
    cur.close()
    conn.close()
    await update.message.reply_text(f"Broadcast done. Sent: {sent}, Failed: {failed}")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM subscribers")
    total = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) as active FROM subscribers WHERE active = TRUE")
    active = cur.fetchone()["active"]
    cur.close()
    conn.close()

    await update.message.reply_text(
        f"Total subscribers: {total}\nActive: {active}\nUnsubscribed: {total - active}"
    )


async def error_handler(update, context):
    logger.error(f"Update {update} caused error: {context.error}")


def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("myreferrals", myreferrals))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))
    app.add_error_handler(error_handler)
    app.run_polling()


if __name__ == "__main__":
    main()
