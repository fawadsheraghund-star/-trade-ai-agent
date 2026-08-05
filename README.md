# Multi-Exchange AI Trading Agent

Features:
- Multi-exchange via CCXT (Binance, Bybit, KuCoin, Gate.io, OKX, and others)
- Telegram bot: commands, inline confirmations
- Urdu voice command support using Whisper (ASR) and gTTS (TTS)
- Technical indicators: EMA, RSI, MACD, Volume
- News sentiment analysis (NewsAPI + Transformers)
- AI analysis (OpenAI; optional)
- Paper trading by default; manual YES required for live trades
- Docker + Railway-friendly

Quickstart:
1. Copy repo and create branch (recommended) e.g., feature/multi-exchange-agent
2. Fill .env or environment variables. Use testnet keys / sandbox keys.
3. Build Docker: docker build -t trade-agent .
4. Run: docker run --env-file .env -p8000:8000 trade-agent
5. Add your Telegram bot token and owner Telegram ID to .env

Security:
- Never commit API keys. Use env vars / Railway secrets.
- Test thoroughly on sandbox/testnet.
