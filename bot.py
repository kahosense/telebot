import asyncio
import logging
import os
from typing import List, Optional

from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

PROMPT_TEMPLATE = """You are helping Louis practice spoken English by converting his daily logs
into natural, conversational English he would actually say out loud.

CRITICAL: This is NOT translation. Generate how Louis would naturally express
these thoughts/events if speaking English casually to a friend.

Guidelines:
- Sound like real speech, not written text
- Keep it casual and natural (contractions, informal grammar OK)
- Preserve the tone and feeling of each entry
- Short entries can stay short ("Had beef brisket noodles yesterday")
- Context-dependent entries (like "36mg") can stay as-is if unclear
- Place names can be romanized or kept in Chinese as he would say them
- Match the original rhythm: short stays short, long stays long
- Preserve any timestamp header lines exactly as-is (e.g. "Life Logging, [2026/2/2 08:46]")
- Output one English entry per input entry, keep blank lines between entries
- Do NOT add new events or explanations

Daily logs:
{user_message}

Natural spoken English version:
"""


def build_prompt(user_message: str) -> str:
    return PROMPT_TEMPLATE.format(user_message=user_message)


def split_message(text: str, limit: int = 3800) -> List[str]:
    if len(text) <= limit:
        return [text]

    parts: List[str] = []
    blocks = text.split("\n\n")
    for block in blocks:
        if not block.strip():
            continue

        if len(block) > limit:
            current = ""
            for line in block.splitlines():
                addition = line + "\n"
                if len(current) + len(addition) > limit:
                    if current.strip():
                        parts.append(current.rstrip())
                    current = ""
                current += addition
            if current.strip():
                parts.append(current.rstrip())
        else:
            if not parts:
                parts.append(block)
            elif len(parts[-1]) + 2 + len(block) <= limit:
                parts[-1] = parts[-1] + "\n\n" + block
            else:
                parts.append(block)

    return [p for p in parts if p.strip()]


def call_openai(client: OpenAI, prompt: str, model: str, temperature: float, max_tokens: int) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content or ""
    return content.strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "Send your daily log entries and I will convert them into natural spoken English."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user_message = update.message.text.strip()
    if not user_message:
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    client: OpenAI = context.application.bot_data["openai_client"]
    model: str = context.application.bot_data["openai_model"]
    temperature: float = context.application.bot_data["openai_temperature"]
    max_tokens: int = context.application.bot_data["openai_max_tokens"]

    try:
        prompt = build_prompt(user_message)
        response_text = await asyncio.to_thread(
            call_openai, client, prompt, model, temperature, max_tokens
        )
    except Exception as e:
        logging.exception(f"LLM request failed: {type(e).__name__}: {str(e)}")
        await update.message.reply_text(
            "Translation failed. Please try again.\n"
            f"Error: {type(e).__name__}"
        )
        return

    if not response_text:
        await update.message.reply_text("No response from LLM.")
        return

    for chunk in split_message(response_text):
        await update.message.reply_text(chunk)


def get_env_str(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def get_env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return float(raw)


def get_env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    # Load .env file if exists (local dev), Railway uses env vars directly
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logging.info("Loaded .env file")
    else:
        logging.info("No .env file found, using environment variables")

    telegram_token = get_env_str("TELEGRAM_BOT_TOKEN")
    openai_api_key = get_env_str("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_temperature = get_env_float("OPENAI_TEMPERATURE", 0.7)
    openai_max_tokens = get_env_int("OPENAI_MAX_TOKENS", 1000)

    # Log configuration
    logging.info("=" * 50)
    logging.info("TeleBot Configuration")
    logging.info("=" * 50)
    logging.info(f"Model: {openai_model}")
    logging.info(f"API Base URL: {openai_base_url}")
    logging.info(f"Temperature: {openai_temperature}")
    logging.info(f"Max Tokens: {openai_max_tokens}")
    logging.info(f"Deployment: {'Railway' if os.getenv('RAILWAY_ENVIRONMENT') else 'Local'}")
    logging.info("=" * 50)

    client = OpenAI(api_key=openai_api_key, base_url=openai_base_url)

    application = Application.builder().token(telegram_token).build()
    application.bot_data["openai_client"] = client
    application.bot_data["openai_model"] = openai_model
    application.bot_data["openai_temperature"] = openai_temperature
    application.bot_data["openai_max_tokens"] = openai_max_tokens

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Auto-detect mode: Webhook for Railway (has PORT env), Polling for local
    use_webhook = os.getenv("PORT") is not None

    if use_webhook:
        # Webhook mode for Railway Free Plan (Serverless compatible)
        port = int(os.environ.get("PORT", 8000))
        webhook_url = os.getenv("WEBHOOK_URL")

        if not webhook_url:
            # Auto-generate from Railway domain if available
            railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
            if railway_domain:
                webhook_url = f"https://{railway_domain}/webhook"
            else:
                raise RuntimeError("WEBHOOK_URL or RAILWAY_PUBLIC_DOMAIN must be set for webhook mode")

        logging.info("=" * 50)
        logging.info("Starting bot in WEBHOOK mode")
        logging.info(f"Port: {port}")
        logging.info(f"Webhook URL: {webhook_url}")
        logging.info("Mode: Railway Free Plan (Serverless compatible)")
        logging.info("=" * 50)

        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="/webhook",
            webhook_url=webhook_url,
            drop_pending_updates=True,
        )
    else:
        # Polling mode for local development
        logging.info("=" * 50)
        logging.info("Starting bot in POLLING mode")
        logging.info("Mode: Local development")
        logging.info("=" * 50)

        application.run_polling(
            close_loop=False,
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )


if __name__ == "__main__":
    main()
