import os
import asyncio
from telegram import __version__ as TG_VER
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from command_parser import parse_command
from trade_engine import TradeEngine
from voice_handler import transcribe_audio, tts_urdu
from utils.logger import logger
import tempfile, aiofiles

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OWNER_ID = int(os.getenv("BOT_OWNER_TELEGRAM_ID", "0"))

engine = TradeEngine(exchange_id=os.getenv("EXCHANGE_ID"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome. I provide analysis & recommendations. Use /recommend SYMBOL or send voice command in Urdu.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "/recommend SYMBOL - get recommendation\n/balance - show balance\n/buy SYMBOL  - start buy flow\n/sell SYMBOL - start sell flow\nSend voice note in Urdu to ask for recommendation."
    await update.message.reply_text(txt)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bal = engine.connector.fetch_balance()
    await update.message.reply_text("Balance fetched. Check logs for details.")
    logger.info("Balance: %s", bal)
    await update.message.reply_text(str(bal.get("total", {}) ))

async def recommend_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /recommend SYMBOL")
        return
    symbol = args[0].upper()
    rec = engine.recommend(symbol)
    # Build the recommendation message safely
    text_lines = [
        f"Recommendation for {symbol}:",
        f"Side: {rec.get('side')}",
        f"Confidence: {rec.get('confidence', 0):.2f}",
        f"Price: {rec.get('last_price')}",
        f"Suggested SL: {rec.get('suggested_sl')}",
        f"Suggested TP: {rec.get('suggested_tp')}",
        f"Suggested Size (value): {rec.get('suggested_size_value')}",
        f"Dry run: {rec.get('dry_run')}",
    ]
    text = "\n".join(text_lines)
    kb = [
        [InlineKeyboardButton("Confirm & Place (Live)", callback_data=f"confirm|{symbol}|{rec.get('side')}|{rec.get('suggested_size_value')}")],
        [InlineKeyboardButton("Dismiss", callback_data="dismiss")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("confirm"):
        parts = data.split("|")
        symbol, side, size = parts[1], parts[2], float(parts[3])
        # secure confirm: only owner allowed for live
        user_id = query.from_user.id
        if str(os.getenv("LIVE_ENABLE", "false")).lower() not in ("1","true","yes"):
            await query.edit_message_text("Live trading disabled. Set LIVE_ENABLE=true to allow real orders.")
            return
        if OWNER_ID != 0 and user_id != OWNER_ID:
            await query.edit_message_text("Only owner can confirm live orders.")
            return
        # place order
        order = engine.place_order(symbol, side, size, order_type="market")
        await query.edit_message_text(f"Order result: {order}")
    elif data == "dismiss":
        await query.edit_message_text("Dismissed.")

async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.voice and not msg.audio:
        await msg.reply_text("Send a voice note (ogg/opus) or audio.")
        return
    file = msg.voice or msg.audio
    f = await file.get_file()
    tmp = tempfile.NamedTemporaryFile(suffix=".oga", delete=False)
    await f.download_to_drive(tmp.name)
    # convert to wav for whisper (ffmpeg required in container)
    wav = tmp.name + ".wav"
    cmd = f"ffmpeg -y -i {tmp.name} -ar 16000 -ac 1 {wav}"
    subprocess = __import__("subprocess")
    subprocess.run(cmd, shell=True, check=False)
    text = transcribe_audio(wav, language="ur")
    parsed = parse_command(text)
    if parsed.get("action") == "analysis":
        rec = engine.recommend(parsed.get("symbol") or "BTC/USDT")
        await msg.reply_text(f"Recommendation: {rec.get('side')} (confidence {rec.get('confidence',0):.2f})")
    elif parsed.get("action") == "trade":
        # show recommendation & require confirm
        rec = engine.recommend(parsed.get("symbol") or "BTC/USDT")
        kb = [[InlineKeyboardButton("Confirm", callback_data=f"confirm|{rec.get('symbol') or parsed.get('symbol','BTC/USDT')}|{rec.get('side')}|{rec.get('suggested_size_value')}")]]
        await msg.reply_text(f"Detected trade request: {parsed}\nRecommend: {rec.get('side')} (conf {rec.get('confidence',0):.2f})", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await msg.reply_text(f"Could not parse: {text}")

def run_bot():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN not provided.")
        return
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("recommend", recommend_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, voice_message_handler))
    logger.info("Starting Telegram bot...")
    app.run_polling()
