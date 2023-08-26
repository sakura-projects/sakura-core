import logging
from typing import TYPE_CHECKING, Callable

from sakura.pubsub.middlewares import Middleware

if TYPE_CHECKING:
    from aio_pika.abc import AbstractIncomingMessage

logger = logging.getLogger(__name__)


class AckMiddleware(Middleware):
    def __init__(self, auto_ack: bool = False):
        self.auto_ack = auto_ack

    def __call__(self, func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            res = await func(*args, **kwargs)

            msg: AbstractIncomingMessage = kwargs.get("__msg")

            if self.auto_ack:
                logger.debug(f"Acknowledged {msg.message_id}")
                await msg.ack()

        return wrapper
