import requests
import uuid
import os
import time
from telegram import Update, InlineQueryResultPhoto
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

COINS = {
    "btc": ("bitcoin", "BTCUSDT"),
    "eth": ("ethereum", "ETHUSDT"),
    "sol": ("solana", "SOLUSDT"),
    "bnb": ("binancecoin", "BNBUSDT"),
    "xrp": ("ripple", "XRPUSDT"),
    "ton": ("the-open-network", "TONUSDT"),
    "usdt": ("tether", "USDTUSDT")
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

# ------------------ CACHE ------------------ #
CACHE = {}
CACHE_TIME = 10

def get_cached(symbol):
    if symbol in CACHE:
        price, change, t = CACHE[symbol]
        if time.time() - t < CACHE_TIME:
            return price, change
    return None, None

def set_cache(symbol, price, change):
    CACHE[symbol] = (price, change, time.time())

# ------------------ COINGECKO ------------------ #
def fetch_coingecko(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={coin_id}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code == 429:
            time.sleep(2)
            return None, None

        data = res.json()
        if not data:
            return None, None

        coin = data[0]
        return coin["current_price"], coin["price_change_percentage_24h"]

    except:
        return None, None

# ------------------ BINANCE ------------------ #
def fetch_binance(symbol):
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"

    try:
        res = requests.get(url, timeout=5).json()
        return float(res["lastPrice"]), float(res["priceChangePercent"])
    except:
        return None, None

# ------------------ MAIN PRICE ------------------ #
def get_price(key):
    coin_id, symbol = COINS[key]

    price, change = get_cached(key)
    if price is not None:
        return price, change

    price, change = fetch_coingecko(coin_id)

    if price is None:
        price, change = fetch_binance(symbol)

    if price is not None:
        set_cache(key, price, change)

    return price, change

# ------------------ FORMAT ------------------ #
def format_price(coin, price, change):
    arrow = "▲" if change >= 0 else "▼"

    return f"""
<b>{coin.upper()} / USD</b>

Price        : ${price:,.4f}
Change       : {arrow} {change:.2f}%
Source       : Multi-API
Market       : Spot

Status       : Active
Update       : Real-time

CurrentRate Terminal
""".strip()

# ------------------ START ------------------ #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_photo(
        photo="https://i.ibb.co/ymc6BrQC/image.png",
        caption=(
            "<b>CurrentRate Terminal</b>\n\n"
            "Premium crypto pricing system.\n\n"
            "Commands:\n"
            "/btc /eth /sol /bnb /xrp /ton /usdt\n"
            "/convert 10 btc\n\n"
            "Inline:\n"
            "@yourbotusername btc\n"
            "@yourbotusername 10 btc"
        ),
        parse_mode="HTML"
    )

# ------------------ COMMAND ------------------ #
async def coin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text.replace("/", "").lower()

    if cmd not in COINS:
        await update.message.reply_text("Invalid asset command.")
        return

    price, change = get_price(cmd)

    if price is None:
        await update.message.reply_text("Unable to retrieve market data.")
        return

    await update.message.reply_photo(
        photo=IMAGES.get(cmd),
        caption=format_price(cmd, price, change),
        parse_mode="HTML"
    )

# ------------------ CONVERT ------------------ #
async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /convert 10 btc")
        return

    try:
        amount = float(context.args[0])
        coin = context.args[1].lower()

        if coin not in COINS:
            await update.message.reply_text("Invalid coin.")
            return

        price, _ = get_price(coin)

        if price is None:
            await update.message.reply_text("Unable to retrieve market data.")
            return

        total = amount * price

        await update.message.reply_photo(
            photo=IMAGES.get(coin),
            caption=f"""
<b>{amount} {coin.upper()}</b>

Value        : ${total:,.2f}
Rate         : ${price:,.4f}

Conversion   : {coin.upper()} → USD
Source       : Multi-API

CurrentRate Terminal
""".strip(),
            parse_mode="HTML"
        )

    except:
        await update.message.reply_text("Usage: /convert 10 btc")

# ------------------ INLINE ------------------ #
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.lower().strip()
    results = []

    parts = query.split()

    # 🔥 INLINE CONVERT (10 btc)
    if len(parts) == 2:
        try:
            amount = float(parts[0])
            coin = parts[1]

            if coin in COINS:
                price, _ = get_price(coin)

                if price:
                    total = amount * price

                    caption = f"""
<b>{amount} {coin.upper()}</b>

Value        : ${total:,.2f}
Rate         : ${price:,.4f}

Conversion   : {coin.upper()} → USD
Source       : Multi-API

CurrentRate Terminal
""".strip()

                    results.append(
                        InlineQueryResultPhoto(
                            id=str(uuid.uuid4()),
                            photo_url=IMAGES.get(coin),
                            thumbnail_url=IMAGES.get(coin),
                            caption=caption,
                            parse_mode="HTML"
                        )
                    )

                    await update.inline_query.answer(results, cache_time=1)
                    return

        except:
            pass

    # 🔥 NORMAL PRICE INLINE
    for coin in COINS.keys():
        if query and coin not in query:
            continue

        price, change = get_price(coin)
        if price is None:
            continue

        results.append(
            InlineQueryResultPhoto(
                id=str(uuid.uuid4()),
                photo_url=IMAGES.get(coin),
                thumbnail_url=IMAGES.get(coin),
                caption=format_price(coin, price, change),
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

    print("Bot running (ULTIMATE VERSION)...")
    app.run_polling()
