SUPPORTED_COINS = {
    "btc": "BTC/USDT",
    "eth": "ETH/USDT",
    "doge": "DOGE/USDT",
    "sol": "SOL/USDT",
    "xrp": "XRP/USDT",
    "ada": "ADA/USDT",
    "bnb": "BNB/USDT",
    "ltc": "LTC/USDT",
    "shib": "SHIB/USDT"
}

import os
import random
import ccxt
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
from threading import Thread

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

def get_signal(symbol):
    exchange = ccxt.binance()
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
        df = pd.DataFrame(bars, columns=["timestamp","open","high","low","close","volume"])
        df["sma_short"] = df["close"].rolling(window=5).mean()
        df["sma_long"] = df["close"].rolling(window=20).mean()

        signal = None
        if df["sma_short"].iloc[-1] > df["sma_long"].iloc[-1]:
            signal = "Buy"
        elif df["sma_short"].iloc[-1] < df["sma_long"].iloc[-1]:
            signal = "Sell"
        return signal, df["close"].iloc[-1]
    except:
        return None, None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Use /signal <coin> to get a crypto signal.\n"
        f"Supported coins: {', '.join(SUPPORTED_COINS.keys())}"
    )

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin_key = (context.args[0].lower() if context.args else "btc")
    if coin_key not in SUPPORTED_COINS:
        await update.message.reply_text(
            "❌ Coin not supported. Try: " + ", ".join(SUPPORTED_COINS.keys())
        )
        return

    symbol = SUPPORTED_COINS[coin_key]
    signal_type, price = get_signal(symbol)
    if signal_type is None or price is None:
        await update.message.reply_text("⚠️ Could not fetch data.")
        return

    emoji = {"Buy": "📈", "Sell": "📉"}.get(signal_type, "")
    await update.message.reply_text(
        f"{emoji} {coin_key.upper()}/USDT\nSignal: {signal_type}\nPrice: ${price:.2f}"
    )

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))

print("🤖 Bot is starting…")
Thread(target=app.run_polling).start()

web_app = Flask('')
@web_app.route('/')
def home():
    return "Bot alive"
Thread(target=web_app.run, kwargs={"host":"0.0.0.0", "port":8080}).start()
