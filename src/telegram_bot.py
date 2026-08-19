from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import os
import logging
from typing import Optional

# Minimal logging
logger = logging.getLogger("trade-ai-agent")
if not logger.handlers:
    h = logging.StreamHandler()
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    h.setFormatter(fmt)
    logger.addHandler(h)
    logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


def detect_symbol(text: str) -> Optional[str]:
    """Try to extract a symbol like BTCUSDT or BTC from free text."""
    import re
    # look for something like BTCUSDT or BTC/USDT or BTC
    m = re.search(r"([A-Za-z]{2,10}USDT)", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m2 = re.search(r"\b([A-Za-z]{2,6})\b", text)
    if m2:
        # return token + USDT as default quote
        return m2.group(1).upper() + "USDT"
    return None


def detect_language(text: str) -> str:
    # crude detection: Devanagari (Hindi) U+0900–U+097F, Arabic script for Urdu U+0600–U+06FF
    if any('\u0900' <= ch <= '\u097F' for ch in text):
        return 'hi'
    if any('\u0600' <= ch <= '\u06FF' for ch in text):
        return 'ur'
    return 'en'


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "/help - show this help\n"
        "/status - provider status (placeholder)\n"
        "/analyze <symbol> - quick analysis for symbol (e.g., /analyze BTCUSDT)\n"
        "/report <symbol> - full market report (placeholder)\n"
        "/test <symbol> - run basic checks (placeholder)\n"
        "You can also ask in natural language, e.g. 'BTC का analysis करो' or 'Bitcoin buy करना चाहिए?'"
    )
    await update.message.reply_text(help_text)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Placeholder status (no market API connected in this step)
    msg = "Provider: no live market provider configured (placeholder)."
    await update.message.reply_text(msg)
    logger.info(f"status command by user={update.effective_user.id}")


async def cmd_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Expect symbol in args
    if context.args:
        symbol = "".join(context.args).upper()
    else:
        await update.message.reply_text("Usage: /analyze SYMBOL (e.g., /analyze BTCUSDT)")
        return
    logger.info(f"/analyze called by {update.effective_user.id} symbol={symbol}")
    # Placeholder analysis response
    resp = (
        f"{symbol} ANALYSIS (PLACEHOLDER)\n"
        "Note: This is paper-trading analysis only. No live market data connected in this step.\n"
        "Signal: WAIT\n"
        "BUY confidence: 0%\n"
        "SELL confidence: 0%\n"
        "Reasons: no data - placeholder.\n"
    )
    await update.message.reply_text(resp)


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Alias to analyze for now but with report label
    if context.args:
        symbol = "".join(context.args).upper()
    else:
        await update.message.reply_text("Usage: /report SYMBOL (e.g., /report BTCUSDT)")
        return
    logger.info(f"/report called by {update.effective_user.id} symbol={symbol}")
    resp = (
        f"{symbol} MARKET REPORT (PLACEHOLDER)\n"
        "Price: N/A\n"
        "Trend: N/A\n"
        "BUY confidence: 0%\n"
        "SELL confidence: 0%\n"
        "WAIT confidence: 100%\n"
        "Signal: WAIT\n"
        "Risk: UNKNOWN\n"
        "Support: N/A\n"
        "Resistance: N/A\n"
        "RSI: N/A\n"
        "MACD: N/A\n"
        "Volume: N/A\n"
        "Possible entry zone: N/A\n"
        "Stop-loss: N/A\n"
        "Target 1: N/A\n"
        "Target 2: N/A\n"
        "Why:\n- No live data in placeholder mode.\n"
        "Invalidation:\n- Live data required.\n"
    )
    await update.message.reply_text(resp)


async def cmd_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        symbol = "".join(context.args).upper()
    else:
        await update.message.reply_text("Usage: /test SYMBOL (e.g., /test BTCUSDT)")
        return
    logger.info(f"/test called by {update.effective_user.id} symbol={symbol}")
    # Placeholder test results
    lines = [f"TEST RESULTS for {symbol} (PLACEHOLDER)"]
    lines.append("market_provider: NOT CONFIGURED")
    lines.append("data_retrieval: SKIPPED")
    lines.append("indicators: SKIPPED")
    lines.append("confidence: SKIPPED")
    lines.append("report: SKIPPED")
    await update.message.reply_text('\n'.join(lines))


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    logger.info(f"text message from {update.effective_user.id}: {text}")
    lang = detect_language(text)

    # Try to detect symbol and intent
    symbol = detect_symbol(text)
    lowered = text.lower()
    if symbol:
        if any(k in lowered for k in ["analysis", "analysis करो", "का analysis", "analysis kar"] ) or any(k in lowered for k in ["analysis", "analysis"]):
            # emulate analyze
            context.args = [symbol]
            await cmd_analyze(update, context)
            return
        if any(k in lowered for k in ["report", "रिपोर्ट", "analysis report"]):
            context.args = [symbol]
            await cmd_report(update, context)
            return
        if any(k in lowered for k in ["buy", "खरीद", "buy करना", "buy करना चाहिए"]):
            # For now reply with placeholder
            await update.message.reply_text(f"{symbol}: I cannot place orders. Use /analyze {symbol} to see placeholder analysis.")
            return
        # default to analyze
        context.args = [symbol]
        await cmd_analyze(update, context)
        return

    await update.message.reply_text("I couldn't detect a symbol or command. Use /help for available commands.")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Placeholder: voice not implemented in this step
    await update.message.reply_text("Voice input will be supported later. For now, send text or use /analyze.")


def run_polling(token: str):
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler('help', cmd_help))
    app.add_handler(CommandHandler('status', cmd_status))
    app.add_handler(CommandHandler('analyze', cmd_analyze))
    app.add_handler(CommandHandler('report', cmd_report))
    app.add_handler(CommandHandler('test', cmd_test))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Starting polling (placeholder command handlers)")
    app.run_polling()
