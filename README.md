# BRT203 Bot

A Telegram marketing/ads bot built with Python, using `python-telegram-bot`.  
Deployed via GitHub → Railway.

**Bot link:** [@BRT203bot](https://t.me/BRT203bot)

## Features
- `/start` — subscribes user, generates a personal referral link
- `/broadcast <message>` — (admin-only) sends a message to all subscribers
- `/stats` — (admin-only) shows total subscriber count

## Tech Stack
- Python 3.11+
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- Hosted on [Railway](https://railway.app)

## Setup

### 1. Clone the repo
\`\`\`bash
git clone https://github.com/beckylinda699-source/brt203-bot.git
cd brt203-bot
\`\`\`

### 2. Install dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 3. Environment variables
Create a `.env` file locally (never commit this):
\`\`\`
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_numeric_id
\`\`\`

### 4. Run locally
\`\`\`bash
python bot.py
\`\`\`

## Deployment
This bot is deployed on Railway, connected directly to this GitHub repo.  
Environment variables (`BOT_TOKEN`, `ADMIN_ID`) are set in Railway's **Variables** tab, not in code.

## Compliance
This bot only messages users who have opted in via `/start`.  
No unsolicited messaging, scraping, or data harvesting is performed, in line with [Telegram's Bot Guidelines](https://core.telegram.org/bots) and [Ad Platform Policy](https://promote.telegram.org).

## License
MIT (or your choice)
