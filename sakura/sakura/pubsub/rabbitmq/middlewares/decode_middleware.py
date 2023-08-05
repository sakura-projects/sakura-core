import logging
from typing import Callable

from sakura.decoders.json_decoder import JSONDecoder
from sakura.pubsub.rabbitmq.middlewares import Middleware

logger = logging.getLogger(__name__)


class DecodeMiddleware(Middleware):
    DEFAULT_CONTENT_TYPE = "application/json"
    DEFAULT_CONTENT_ENCODING = "utf-8"

    decoders = {
        "application/json": JSONDecoder()
    }

    def __call__(self, func: Callable) -> Callable:
        async def wrapper(msg):
            if not msg.content_type or not msg.content_encoding:
                logger.warning(f"Missing content_type or content_encoding in {msg.message_id=}, assuming defaults")
                msg.content_type = DecodeMiddleware.DEFAULT_CONTENT_TYPE
                msg.content_encoding = DecodeMiddleware.DEFAULT_CONTENT_ENCODING

            request_body = DecodeMiddleware.decoders.get(msg.content_type).decode(msg.body.decode(msg.content_encoding))

            return await func(request_body)

        return wrapper
