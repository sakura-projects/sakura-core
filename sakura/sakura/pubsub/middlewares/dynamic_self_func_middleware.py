from typing import Callable

from sakura.pubsub.middlewares.middleware import Middleware
from sakura.utils.decorators import DynamicSelfFunc


class DynamicSelfFuncMiddleware(Middleware):
    def __call__(self, func: Callable) -> Callable:
        return DynamicSelfFunc(func)()
