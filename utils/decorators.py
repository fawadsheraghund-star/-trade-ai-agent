import os
import time
import functools
import asyncio
from typing import Callable, Any
from utils.logger import logger


def _is_truthy_env(var: str) -> bool:
    return str(os.getenv(var, "")).lower() in ("1", "true", "yes")


def _extract_user_id(*args, **kwargs):
    # Look for explicit user_id kwarg
    if "user_id" in kwargs:
        return kwargs.get("user_id")
    # Try common telegram objects
    if args:
        first = args[0]
        # If passed a numeric id
        if isinstance(first, int):
            return first
        # Try Update-like objects: effective_user or from_user
        try:
            u = getattr(first, "effective_user", None)
            if u and getattr(u, "id", None):
                return u.id
        except Exception:
            pass
        try:
            u = getattr(first, "from_user", None)
            if u and getattr(u, "id", None):
                return u.id
        except Exception:
            pass
        # callback_query
        try:
            cq = getattr(first, "callback_query", None)
            if cq:
                u = getattr(cq, "from_user", None)
                if u and getattr(u, "id", None):
                    return u.id
        except Exception:
            pass
    return None


def owner_only(func: Callable) -> Callable:
    """Decorator that raises PermissionError when caller is not the configured owner.

    The wrapped function must be called with either a keyword argument `user_id` or with
    an Update-like object as the first positional argument so the decorator can extract
    the user's id.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        owner = os.getenv("BOT_OWNER_TELEGRAM_ID", "0")
        user_id = _extract_user_id(*args, **kwargs)
        try:
            owner_int = int(owner)
        except Exception:
            owner_int = 0
        if owner_int != 0 and user_id != owner_int:
            logger.warning("Unauthorized user: %s tried to call %s", user_id, func.__name__)
            raise PermissionError("Only owner can perform this action")
        return func(*args, **kwargs)
    # support async funcs
    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def awrapper(*args, **kwargs):
            owner = os.getenv("BOT_OWNER_TELEGRAM_ID", "0")
            user_id = _extract_user_id(*args, **kwargs)
            try:
                owner_int = int(owner)
            except Exception:
                owner_int = 0
            if owner_int != 0 and user_id != owner_int:
                logger.warning("Unauthorized user: %s tried to call %s", user_id, func.__name__)
                raise PermissionError("Only owner can perform this action")
            return await func(*args, **kwargs)
        return awrapper
    return wrapper


def require_live(func: Callable) -> Callable:
    """Decorator that prevents running when LIVE_ENABLE is not set to a truthy value.

    If LIVE_ENABLE is falsy, raises RuntimeError.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not _is_truthy_env("LIVE_ENABLE"):
            logger.warning("Attempted live operation while LIVE_ENABLE is false: %s", func.__name__)
            raise RuntimeError("Live trading is disabled. Set LIVE_ENABLE=true to enable.")
        return func(*args, **kwargs)
    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def awrapper(*args, **kwargs):
            if not _is_truthy_env("LIVE_ENABLE"):
                logger.warning("Attempted live operation while LIVE_ENABLE is false: %s", func.__name__)
                raise RuntimeError("Live trading is disabled. Set LIVE_ENABLE=true to enable.")
            return await func(*args, **kwargs)
        return awrapper
    return wrapper


def retry(on_exceptions=(Exception,), attempts: int = 3, backoff: float = 1.0):
    """Retry decorator with simple exponential backoff.

    Usage: @retry(attempts=5, backoff=2)
    """
    def deco(func: Callable):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def awrap(*args, **kwargs):
                last_exc = None
                for i in range(attempts):
                    try:
                        return await func(*args, **kwargs)
                    except on_exceptions as e:
                        last_exc = e
                        delay = backoff * (2 ** i)
                        logger.warning("Retry %s/%s after exception: %s (sleep %s)", i+1, attempts, e, delay)
                        await asyncio.sleep(delay)
                logger.error("Operation failed after %s attempts: %s", attempts, last_exc)
                raise last_exc
            return awrap
        else:
            @functools.wraps(func)
            def wrap(*args, **kwargs):
                last_exc = None
                for i in range(attempts):
                    try:
                        return func(*args, **kwargs)
                    except on_exceptions as e:
                        last_exc = e
                        delay = backoff * (2 ** i)
                        logger.warning("Retry %s/%s after exception: %s (sleep %s)", i+1, attempts, e, delay)
                        time.sleep(delay)
                logger.error("Operation failed after %s attempts: %s", attempts, last_exc)
                raise last_exc
            return wrap
    return deco


def safe_async(func: Callable) -> Callable:
    """Wrap async function to catch and log exceptions and avoid crashing the caller."""
    if not asyncio.iscoroutinefunction(func):
        return func
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.exception("Exception in async function %s: %s", func.__name__, e)
            return None
    return wrapper
