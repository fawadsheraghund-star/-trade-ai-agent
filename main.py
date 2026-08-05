import os
import threading
from telegram_bot import run_bot
from fastapi import FastAPI
from utils.logger import logger

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    # Start telegram bot in background thread and run FastAPI for web hooks/health
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    import uvicorn
    logger.info("Starting API server")
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=False)
