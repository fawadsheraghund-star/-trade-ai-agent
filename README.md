# Multi-Exchange AI Trading Agent

Features
- Multi-exchange via CCXT (Binance, Bybit, KuCoin, Gate.io, OKX, and others)
- Telegram bot: commands, inline confirmations
- Urdu voice command support using Whisper (ASR) and gTTS (TTS)
- Technical indicators: EMA, RSI, MACD, Volume
- News sentiment analysis (NewsAPI + Transformers)
- AI analysis (OpenAI; optional)
- Paper trading by default; manual YES required for live trades
- Docker + Railway-friendly

## Quickstart (local development, TEST MODE)
1. Clone the repo and checkout the branch for development (recommended):
   git clone https://github.com/fawadsheraghund-star/-trade-ai-agent.git
   cd -trade-ai-agent
   git checkout feature/multi-exchange-agent

2. Create and activate a Python virtual environment:
   python3 -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   # Windows (PowerShell): .\.venv\Scripts\Activate.ps1

3. Install dependencies (if requirements.txt present):
   pip install --upgrade pip
   pip install -r requirements.txt

   If requirements.txt is not present, install a minimal test set:
   pip install uvicorn[standard] fastapi python-telegram-bot==20.3 ccxt pandas httpx aiofiles

4. Prepare environment variables (copy and edit .env.example):
   cp .env.example .env
   # Important: For TEST MODE, ensure these settings:
   USE_TESTNET=true
   LIVE_ENABLE=false
   TELEGRAM_TOKEN=         # leave empty for safe dry run OR set to a test bot token
   BOT_OWNER_TELEGRAM_ID=0
   PORT=8000

5. Create data directory for persistence:
   mkdir -p data

6. Run the application (recommended for dev/test):
   python main.py

   Note: `main.py` starts the Telegram bot thread (when run directly) and then runs uvicorn. Running `uvicorn main:app` will start only the API server (FastAPI) and will NOT start the Telegram bot thread.

## Commands (Telegram handlers)
- /start — welcome message and basic usage
- /help — command list and descriptions
- /recommend SYMBOL — get a market recommendation (example: `/recommend BTC/USDT`)
- /balance — fetch account balances (from connector or stub)
- /buy SYMBOL, /sell SYMBOL — start a buy/sell flow that produces a proposal (requires manual confirm for live)
- Voice notes — send an OGG/opus voice note (Urdu) to request analysis or trades (requires voice handler present)

Note: If TELEGRAM_TOKEN is empty, the bot will not connect to Telegram. Use a test bot token for interactive testing.

## Test mode usage
- Always keep the environment in TEST MODE while developing and testing:
  - USE_TESTNET=true
  - LIVE_ENABLE=false
- Recommended safe settings for local testing:
  - TELEGRAM_TOKEN= (empty) — prevents sending messages
  - BOT_OWNER_TELEGRAM_ID=0 — disables owner-only live confirmations
- Use provided stubs (ccxt_connector.py, voice_handler.py, security.py) for offline/local tests if exchange connectors or ASR/TTS modules are not present.
- Validate analysis and recommendation flows by calling TradeEngine.recommend() in a REPL:
  python - <<'PY'
  from trade_engine import TradeEngine
  e = TradeEngine('mock')
  print(e.recommend('BTC/USDT'))
  PY

## Running in Docker (TEST MODE)
1. Build image:
   docker build -t trade-agent .
2. Ensure .env contains TEST MODE settings and is not committed.
3. Run container (maps port 8000):
   docker run --env-file .env -p8000:8000 trade-agent

Or use docker-compose (if docker-compose.yml present):
   docker-compose build
   docker-compose up

Note: Ensure a persistent volume for `data/` is configured so history and audit logs survive restarts.

## Safety notes (MANDATORY)
- LIVE trading MUST remain disabled until you complete security review and staging tests:
  - LIVE_ENABLE=false (do NOT set to true in repo or commits)
  - Store exchange API keys in a secure secrets manager (AWS/GCP/Azure/Platform secrets). Do NOT commit keys.
  - API keys should have least privilege (no withdrawals) and be limited by IP if exchange supports it.
- Manual confirmation: all live orders must require owner confirmation (one-time token or owner-only Telegram callback).
- Audit logging: enable persistent SECURITY_AUDIT_LOG (default: data/security_audit.log) and monitor it.
- Test on exchange testnets (Binance Testnet, Bybit Testnet) before any live run.
- Implement circuit breakers (MAX_ORDER_PCT, DAILY_MAX_DRAWDOWN) before turning on live mode.

## Project layout (key files)
- main.py — app entrypoint (starts bot thread and FastAPI)
- telegram_bot.py — Telegram handlers and voice handling glue
- trade_engine.py — analysis and recommendation engine
- ccxt_connector.py — exchange connector (use real implementation or test stub)
- alerts.py, scheduler.py — scheduled checks and alert handlers
- history.py — trade history logging (SQLite)
- LIVE_SETUP.md, LIVE_TRADING.md — live setup & safety documentation
- TESTING_CHECKLIST.md — user testing checklist for TEST MODE

## Troubleshooting
- Syntax/Import errors: run `python -m py_compile $(git ls-files '*.py')` and fix the reported file.
- Missing modules: ensure stubs or real implementations exist (ccxt_connector.py, voice_handler.py).
- Bot not starting: run `python main.py` (starts bot thread). Running `uvicorn main:app` alone will not start the Telegram bot thread.
- Health check: curl http://127.0.0.1:8000/health → {"status":"ok"}

## Contributing
- Work on feature branches and open PRs to merge into main.
- Do not enable live trading in PRs — keep LIVE_ENABLE=false in code and .env.example.

## License & Authors
- Author: fawadsheraghund-star
- Maintainer: fawadsheraghund-star

