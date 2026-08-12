import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    name = user.first_name if user else "there"
    await update.message.reply_text(f"Hello {name}! Bot is up and running.")


def run_polling(token: str) -> None:
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start_command))
    print("Starting Telegram bot (polling)...")
    app.run_polling()
