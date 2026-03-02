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
CART_API_URL = os.getenv("BOT_CART_API_URL", "http://cart_api:8001/api/v1")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Напиши, что добавить в корзину. Команды: /cart, /clear"
    )


async def relay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payload = {"user_id": str(update.effective_user.id), "message": update.message.text}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(AGENT_API_URL, json=payload)
        resp.raise_for_status()
        reply = resp.json()["reply"]
    await update.message.reply_text(reply)


async def cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{CART_API_URL}/carts/by-user/{user_id}/latest")

    if resp.status_code == 404:
        await update.message.reply_text("Корзина пока пустая.")
        return

    resp.raise_for_status()
    data = resp.json()
    if not data["items"]:
        await update.message.reply_text("Корзина пустая.")
        return

    lines = ["Ваша корзина:"]
    for item in data["items"]:
        lines.append(
            f"- {item['title']} x{item['qty']} = {item['qty'] * item['unit_price']:.2f} ₽"
        )
    lines.append(f"Итого: {data['total_amount']} ₽")
    await update.message.reply_text("\n".join(lines))


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    async with httpx.AsyncClient(timeout=15) as client:
        latest = await client.get(f"{CART_API_URL}/carts/by-user/{user_id}/latest")
        if latest.status_code == 404:
            await update.message.reply_text("Корзина уже пустая.")
            return
        latest.raise_for_status()
        cart_id = latest.json()["cart_id"]
        resp = await client.delete(f"{CART_API_URL}/carts/{cart_id}/items")
        resp.raise_for_status()

    await update.message.reply_text("Корзина очищена.")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is required")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cart", cart))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay))
    app.run_polling()


if __name__ == "__main__":
    main()
