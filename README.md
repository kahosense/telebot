# Daily Log Translation Bot (Telegram)

This bot converts your mixed-language daily logs into natural, conversational English for speaking practice.

## Features

- Receives log batches via Telegram
- Sends them to OpenAI for conversion (not literal translation)
- Returns a natural, spoken-English version
- Keeps timestamp headers like `Life Logging, [2026/2/2 08:46]`

## Setup (macOS)

1) Open Terminal
2) Create a virtual environment and install dependencies:

```bash
cd /Users/louis/Coding/projects/TeleBot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3) Configure keys (copy and edit):

```bash
cp .env.example .env
```

Open `.env` and fill in:

- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL` (your custom API endpoint, e.g. `https://api.laozhang.ai/v1`)

4) Run the bot:

```bash
python bot.py
```

Stop with `Ctrl+C`.

## Notes

- The bot runs locally with long polling (no webhook needed).
- If you plan to deploy to cloud later, this structure still works.

## Troubleshooting

- If nothing happens, check that your bot token and OpenAI key are correct.
- If Telegram messages are too long, the bot will split output into multiple messages automatically.
