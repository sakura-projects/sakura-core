import asyncio
import functools
from typing import Callable

import asyncer

from sakura.pubsub.middlewares.middleware import Middleware


class AsyncifyMiddleware(Middleware):
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            func_ = asyncer.asyncify(func) if not asyncio.iscoroutinefunction(func) else func

            return await func_(*args, **kwargs)

        return wrapper
