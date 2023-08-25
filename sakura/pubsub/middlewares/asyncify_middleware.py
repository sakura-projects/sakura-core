import asyncio
from typing import Callable

import asyncer

from sakura.pubsub.middlewares.middleware import Middleware


class AsyncifyMiddleware(Middleware):
    def __call__(self, func: Callable) -> Callable:
        if not asyncio.iscoroutinefunction(func):
            func = asyncer.asyncify(func)

        return func
