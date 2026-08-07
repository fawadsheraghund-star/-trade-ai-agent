import sys
import os
from src.config import settings
from src.telegram_bot import run_polling


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or settings.TELEGRAM_BOT_TOKEN
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN is not set. Populate .env or set env var.")
        sys.exit(1)

    # For Phase 1 we use polling mode. TELEGRAM_USE_WEBHOOK support will be added later.
    run_polling(token)


if __name__ == "__main__":
    main()
