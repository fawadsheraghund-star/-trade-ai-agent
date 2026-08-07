# Railway deployment notes for Phase 1

For Phase 1 the Telegram bot runs in polling mode (background worker). Railway can run this as a Worker service.

Steps:
1. Create a new Railway project and link this GitHub repo.
2. Create a Worker service (not HTTP) or set the service to run the command: python src/main.py
3. Set the environment variables in Railway:
   - TELEGRAM_BOT_TOKEN (required)
   - TELEGRAM_USE_WEBHOOK (false)
   - PORT (optional)
   - SECRET_KEY (recommended)
4. Deploy. The Worker will start and run the polling loop. Check logs in Railway to see bot startup.

Notes on webhook support:
- Webhook support will be implemented in later phases. When using webhooks, configure a Web service with an HTTP endpoint and set TELEGRAM_USE_WEBHOOK=true and TELEGRAM_WEBHOOK_URL to the Railway-provided domain.

