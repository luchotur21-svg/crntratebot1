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

# 🔐 Secure token (Railway ENV)
BOT_TOKEN = os.getenv("BOT_TOKEN")

COINS = {
    "btc": "BTCUSDT",
    "eth": "ETHUSDT",
    "sol": "SOLUSDT",
    "bnb": "BNBUSDT",
    "xrp": "XRPUSDT",
    "ton": "TONUSDT",
    "usdt": "USDTUSDT"
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
def get_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    try:
        res = requests.get(url, timeout=5).json()
        price = float(res["lastPrice"])
        change = float(res["priceChangePercent"])
        return price, change
    except:
        return None, None


# ------------------ FORMAT ------------------ #
def format_price(symbol, price, change):
    coin = symbol[:-4]
    arrow = "▲" if change >= 0 else "▼"

    return f"""
<b>{coin} / USD</b>

Price        : ${price:,.4f}
Change       : {arrow} {change:.2f}%
Exchange     : Binance
Market Type  : Spot
Status       : Active
Update       : Real-time

CurrentRate Terminal
""".strip()


def format_inline(symbol, price, change):
    coin = symbol[:-4]
    arrow = "▲" if change >= 0 else "▼"

    return f"""
<b>{coin} / USD</b>

Price        : ${price:,.4f}
Change       : {arrow} {change:.2f}%
Exchange     : Binance
Market Type  : Spot
Status       : Active
Update       : Real-time
""".strip()


# ------------------ START ------------------ #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = (
        "<b>CurrentRate Terminal</b>\n\n"
        "Real-time digital asset pricing interface.\n\n"
        "Use commands:\n"
        "/btc /eth /sol /bnb /xrp /ton /usdt\n\n"
        "Inline usage:\n"
        "@yourbotusername btc"
    )

    banner = "https://i.ibb.co/ymc6BrQC/image.png"

    await update.message.reply_photo(
        photo=banner,
        caption=caption,
        parse_mode="HTML"
    )


# ------------------ COMMAND ------------------ #
async def coin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text.replace("/", "").lower()

    if command in COINS:
        symbol = COINS[command]
        price, change = get_price(symbol)

        if price is None:
            await update.message.reply_text("Unable to retrieve market data.")
            return

        caption = format_price(symbol, price, change)
        image = IMAGES.get(command)

        await update.message.reply_photo(
            photo=image,
            caption=caption,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("Invalid asset command.")


# ------------------ INLINE ------------------ #
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.lower().strip()
    results = []

    def build_result(symbol_key, symbol):
        price, change = get_price(symbol)
        if price is None:
            return None

        image = IMAGES.get(symbol_key)
        message = format_inline(symbol, price, change)

        return InlineQueryResultPhoto(
            id=str(uuid.uuid4()),
            photo_url=image,
            thumbnail_url=image,
            caption=message,
            parse_mode="HTML"
        )

    if query in COINS:
        result = build_result(query, COINS[query])
        if result:
            results.append(result)
    else:
        for key, symbol in COINS.items():
            result = build_result(key, symbol)
            if result:
                results.append(result)

    await update.inline_query.answer(results, cache_time=1)


# ------------------ MAIN ------------------ #
if __name__ == "__main__":
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    for coin in COINS.keys():
        app.add_handler(CommandHandler(coin, coin_command))

    app.add_handler(InlineQueryHandler(inline_query))

    print("Bot running on Railway...")
    app.run_polling()
