import functools
import logging
from typing import Callable

from sakura.pubsub.middlewares.middleware import Middleware

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware(Middleware):
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:  # noqa: BLE001
                logger.error(f"An error occurred in {func.__name__} resolution", exc_info=e)                

        return wrapper
