from typing import Callable

from sakura.pubsub.rabbitmq.middlewares import Middleware
from sakura.utils.decorators import DynamicSelfFunc


class DynamicSelfFuncMiddleware(Middleware):
    def __call__(self, func: Callable) -> Callable:
        return DynamicSelfFunc(func)()
