import logging
import os
from logging import Logger

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def _make_logger(name: str = None) -> Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        level = getattr(logging, LOG_LEVEL, logging.INFO)
        logger.setLevel(level)
        ch = logging.StreamHandler()
        ch.setLevel(level)
        fmt = os.getenv("LOG_FORMAT", "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        formatter = logging.Formatter(fmt)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        # Avoid message duplication when root logger configured elsewhere
        logger.propagate = False
    return logger

# module-level logger for convenience
logger = _make_logger("trade_agent")

if __name__ == "__main__":
    logger.info("Logger initialized at level %s", LOG_LEVEL)
