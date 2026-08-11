import os
import sys
import hashlib
import atexit
import signal
from pathlib import Path

# Ensure the repository root (parent of src/) is on sys.path so imports like
# `from src.config import settings` work when running `python src/main.py`.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.config import settings
from src.telegram_bot import run_polling


def _create_lockfile_for_token(token: str) -> Path:
    # Use a hash of the token so we don't expose secrets in filenames.
    h = hashlib.sha256(token.encode("utf-8")).hexdigest()
    lockfile = Path(f"/tmp/telegram_polling_{h}.lock")

    # Try to create the lockfile atomically. If it already exists, assume another
    # polling instance is running on this host and exit gracefully.
    try:
        # Use os.O_EXCL to ensure creation fails if file exists.
        fd = os.open(str(lockfile), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        print(
            f"Another Telegram polling process appears to be running (lockfile={lockfile}). Exiting to avoid getUpdates conflict."
        )
        sys.exit(0)

    # Ensure lockfile is removed on process exit.
    def _cleanup() -> None:
        try:
            if lockfile.exists():
                lockfile.unlink()
        except Exception:
            pass

    atexit.register(_cleanup)

    # Also handle termination signals to remove the lockfile immediately.
    def _handle_signal(signum, frame):
        _cleanup()
        sys.exit(0)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handle_signal)
        except Exception:
            # Some environments may not allow setting signal handlers; ignore.
            pass

    return lockfile


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or settings.TELEGRAM_BOT_TOKEN
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN is not set. Populate .env or set env var.")
        sys.exit(1)

    # If TELEGRAM_USE_WEBHOOK is enabled, do not start polling. Webhook mode will
    # be implemented later; in the meantime avoid running polling when webhooks
    # are expected (prevents accidental multiple polling instances).
    env_use_webhook = os.environ.get("TELEGRAM_USE_WEBHOOK")
    use_webhook = (
        (env_use_webhook is not None and env_use_webhook.lower() in ("1", "true", "yes"))
        or bool(settings.TELEGRAM_USE_WEBHOOK)
    )
    if use_webhook:
        print("TELEGRAM_USE_WEBHOOK is set; not starting polling. Exiting.")
        return

    # Create a host-local lockfile so only one polling process runs on the host.
    # This prevents the Telegram "terminated by other getUpdates request" error
    # when the same host accidentally starts the bot twice.
    _create_lockfile_for_token(token)

    # For Phase 1 we use polling mode. TELEGRAM_USE_WEBHOOK support will be added later.
    run_polling(token)


if __name__ == "__main__":
    main()
