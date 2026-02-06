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
    except Exception:
        logging.exception("LLM request failed")
        await update.message.reply_text("Translation failed. Please try again.")
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

    env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(env_path)

    telegram_token = get_env_str("TELEGRAM_BOT_TOKEN")
    openai_api_key = get_env_str("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_temperature = get_env_float("OPENAI_TEMPERATURE", 0.7)
    openai_max_tokens = get_env_int("OPENAI_MAX_TOKENS", 1000)

    logging.info(f"Using model: {openai_model}")
    logging.info(f"API base URL: {openai_base_url}")

    client = OpenAI(api_key=openai_api_key, base_url=openai_base_url)

    application = Application.builder().token(telegram_token).build()
    application.bot_data["openai_client"] = client
    application.bot_data["openai_model"] = openai_model
    application.bot_data["openai_temperature"] = openai_temperature
    application.bot_data["openai_max_tokens"] = openai_max_tokens

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Bot started. Press Ctrl+C to stop.")
    application.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
