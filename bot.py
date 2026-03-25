 import requests
import uuid
import os
from telegram import Update, InlineQueryResultPhoto
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

COINS = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "bnb": "binancecoin",
    "xrp": "ripple",
    "ton": "the-open-network",
    "usdt": "tether"
}

IMAGES = {
    "btc": "https://i.ibb.co/Hcct9JJ/image.png",
    "ton": "https://i.ibb.co/m5rNpssJ/image.png",
    "sol": "https://i.ibb.co/qF5VvKRr/image.png",
    "eth": "https://i.ibb.co/TBxxdNS4/image.png",
    "usdt": "https://i.ibb.co/mjrbQVb/image.png",
    "bnb": "https://i.ibb.co/GQXV7t4P/image.png",
    "xrp": "https://i.ibb.co/M5BMh071/image.png"
}

# ------------------ PRICE FETCH ------------------ #
def get_price(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={coin_id}"
    try:
        data = requests.get(url, timeout=5).json()[0]
        return data["current_price"], data["price_change_percentage_24h"]
    except:
        return None, None


# ------------------ FORMAT ------------------ #
def format_price(coin, price, change):
    arrow = "▲" if change >= 0 else "▼"

    return f"""
<b>{coin.upper()} / USD</b>

Price        : ${price:,.4f}
Change       : {arrow} {change:.2f}%
Source       : CoinGecko
Market       : Spot

Status       : Active
Update       : Real-time

CurrentRate Terminal
""".strip()


# ------------------ START ------------------ #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = (
        "<b>CurrentRate Terminal</b>\n\n"
        "Live crypto pricing & conversion system.\n\n"
        "Commands:\n"
        "/btc /eth /sol /bnb /xrp /ton /usdt\n"
        "/convert 10 btc\n\n"
        "Inline:\n"
        "@yourbotusername btc"
    )

    await update.message.reply_photo(
        photo="https://i.ibb.co/ymc6BrQC/image.png",
        caption=caption,
        parse_mode="HTML"
    )


# ------------------ PRICE COMMAND ------------------ #
async def coin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text.replace("/", "").lower()

    if command in COINS:
        coin_id = COINS[command]
        price, change = get_price(coin_id)

        if price is None:
            await update.message.reply_text("Unable to retrieve market data.")
            return

        caption = format_price(command, price, change)

        await update.message.reply_photo(
            photo=IMAGES.get(command),
            caption=caption,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("Invalid asset command.")


# ------------------ CONVERT COMMAND ------------------ #
async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage: /convert <amount> <coin>\nExample: /convert 10 btc"
        )
        return

    try:
        amount = float(context.args[0])
        coin = context.args[1].lower()

        if coin not in COINS:
            await update.message.reply_text("Invalid coin symbol.")
            return

        price, _ = get_price(COINS[coin])

        if price is None:
            await update.message.reply_text("Unable to retrieve market data.")
            return

        total = amount * price

        caption = f"""
<b>{amount} {coin.upper()}</b>

Value        : ${total:,.2f}
Rate         : ${price:,.4f}

Conversion   : {coin.upper()} → USD
Source       : CoinGecko

CurrentRate Terminal
""".strip()

        await update.message.reply_photo(
            photo=IMAGES.get(coin),
            caption=caption,
            parse_mode="HTML"
        )

    except ValueError:
        await update.message.reply_text(
            "Invalid number. Example: /convert 10 btc"
        )


# ------------------ INLINE ------------------ #
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.lower().strip()
    results = []

    for coin, coin_id in COINS.items():
        if query and coin not in query:
            continue

        price, change = get_price(coin_id)
        if price is None:
            continue

        message = format_price(coin, price, change)

        results.append(
            InlineQueryResultPhoto(
                id=str(uuid.uuid4()),
                photo_url=IMAGES.get(coin),
                thumbnail_url=IMAGES.get(coin),
                caption=message,
                parse_mode="HTML"
            )
        )

    await update.inline_query.answer(results, cache_time=1)


# ------------------ MAIN ------------------ #
if __name__ == "__main__":
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("convert", convert))

    for coin in COINS.keys():
        app.add_handler(CommandHandler(coin, coin_command))

    app.add_handler(InlineQueryHandler(inline_query))

    print("Bot running (FINAL VERSION)...")
    app.run_polling()
