import os

import httpx
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

AGENT_API_URL = os.getenv(
    "BOT_AGENT_API_URL", "http://agent_api:8000/api/v1/agent/intent"
)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши, что добавить в корзину.")


async def relay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payload = {"user_id": str(update.effective_user.id), "message": update.message.text}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(AGENT_API_URL, json=payload)
        resp.raise_for_status()
        reply = resp.json()["reply"]
    await update.message.reply_text(reply)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is required")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay))
    app.run_polling()


if __name__ == "__main__":
    main()
