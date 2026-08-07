import os
import sys

# Ensure the repository root (parent of src/) is on sys.path so imports like
# `from src.config import settings` work when running `python src/main.py`.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

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
