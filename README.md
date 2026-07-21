# BRT203 Bot

A Telegram marketing/ads bot built with Python, using `python-telegram-bot` and PostgreSQL.  
Deployed via GitHub → Railway.

**Bot link:** [@BRT203bot](https://t.me/BRT203bot)

## Features
- `/start` — subscribes user, generates a personal referral link
- `/stop` — unsubscribes user (soft delete, preserves referral history)
- `/myreferrals` — shows how many people a user has referred
- `/help` — lists available commands
- `/broadcast <message>` — (admin-only) rate-limited broadcast to active subscribers
- `/stats` — (admin-only) shows total/active/unsubscribed counts

## Tech Stack
- Python 3.12
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- PostgreSQL (Railway-managed)
- Hosted on [Railway](https://railway.app)

## Environment Variables (set in Railway, not in code)
- `BOT_TOKEN` — from @BotFather
- `ADMIN_ID` — your numeric Telegram user ID
- `DATABASE_URL` — reference to Railway's PostgreSQL plugin: `${{Postgres.DATABASE_URL}}`

## Setup (local development)

\`\`\`bash
git clone https://github.com/beckylinda699-source/brt203-bot.git
cd brt203-bot
pip install -r requirements.txt
\`\`\`

Create a `.env` file locally (never commit this):
\`\`\`
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_numeric_id
DATABASE_URL=your_local_or_test_postgres_url
\`\`\`

Run:
\`\`\`bash
python bot.py
\`\`\`

## Deployment
1. Push code to this GitHub repo — Railway auto-deploys from `main`
2. Add the PostgreSQL plugin in Railway (creates its own `DATABASE_URL`)
3. In the bot service's **Variables** tab, add `DATABASE_URL` as a reference: `${{Postgres.DATABASE_URL}}`
4. Add `BOT_TOKEN` and `ADMIN_ID` as regular variables

## Compliance
This bot only messages users who have opted in via `/start` and honors `/stop` immediately.  
No unsolicited messaging, scraping, or data harvesting, in line with [Telegram's Bot Guidelines](https://core.telegram.org/bots) and [Ad Platform Policy](https://promote.telegram.org).

## License
MIT
