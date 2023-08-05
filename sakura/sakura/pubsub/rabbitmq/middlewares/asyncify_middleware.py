import asyncio
from typing import Callable

import asyncer

from sakura.pubsub.rabbitmq.middlewares import Middleware


class AsyncifyMiddleware(Middleware):
    def __call__(self, func: Callable) -> Callable:
        if not asyncio.iscoroutinefunction(func):
            func = asyncer.asyncify(func)

        return func
