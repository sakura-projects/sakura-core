import logging
from typing import Callable

from aio_pika.abc import AbstractIncomingMessage

from sakura.pubsub.rabbitmq.middlewares import Middleware

logger = logging.getLogger(__name__)


class AckMiddleware(Middleware):
    def __init__(self, auto_ack: bool = False):
        self.auto_ack = auto_ack

    def __call__(self, func: Callable) -> Callable:
        async def wrapper(msg: AbstractIncomingMessage):
            result = await func(msg)
            if self.auto_ack:
                await msg.ack()

            return result

        return wrapper
