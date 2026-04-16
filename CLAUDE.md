# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run locally (polling mode)
python bot.py

# Run tests
python test_mode_detection.py

# macOS: double-click or run start_bot.command to launch bot in terminal
```

The bot auto-detects its run mode: if `PORT` env var is set (Railway), it uses webhook mode; otherwise it uses long polling (local dev).

## Architecture

Single-file bot ([bot.py](bot.py)) using `python-telegram-bot` with an OpenAI-compatible backend.

**Request flow:**
1. Telegram message arrives → `handle_message()`
2. Language detected via `detect_language()` — any CJK character = Chinese input
3. Mode check: if `/topic` was issued previously (`context.user_data["mode"] == "topic"`), use structured dialogue prompt; else auto-route CN→EN or EN→CN
4. `call_openai()` is called in a thread via `asyncio.to_thread()` (sync OpenAI client, async handler)
5. Response split into ≤3800-char chunks by `split_message()` and sent back

**Three prompt modes:**
- `PROMPT_TEMPLATE` — CN→EN spoken conversion (default for Chinese input)
- `EN_TO_CN_PROMPT_TEMPLATE` — EN→CN spoken conversion (default for English input)
- `TOPIC_PROMPT_TEMPLATE` — structured dialogue practice triggered by `/topic` command; one-shot mode (mode is popped after use)

**Config via env vars** (loaded from `.env` locally, injected directly on Railway):
- `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY` — required
- `OPENAI_BASE_URL` — custom API endpoint (supports non-OpenAI providers via OpenAI-compatible API)
- `OPENAI_MODEL` — default `gpt-4o-mini`
- `OPENAI_TEMPERATURE`, `OPENAI_MAX_TOKENS` — tuning params

## Deployment

- **Local**: runs as polling; `.env` file required
- **Railway**: webhook mode auto-activated when `PORT` env var present; `RAILWAY_PUBLIC_DOMAIN` used to auto-generate webhook URL; no `WEBHOOK_URL` needed if the domain is set. See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for full steps.
