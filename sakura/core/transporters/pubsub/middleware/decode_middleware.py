import logging

from sakura.core.exceptions import DecodeError
from sakura.core.pubsub.types import PubSubRequest, PubSubApp
from sakura.core.decoders import JSONDecoder
from sakura.core.utils.types import DecoratedCallable

logger = logging.getLogger(__name__)


class DecodeMiddleware(PubSubApp):
    decoders = {
        "application/json": JSONDecoder()
    }

    DEFAULT_CONTENT_TYPE = "application/json"
    DEFAULT_CONTENT_ENCODING = "utf-8"

    def __init__(self, app: PubSubApp):
        self.app = app

    async def __call__(self, request: PubSubRequest, handler: DecoratedCallable):
        if not request.content_type or not request.content_encoding:
            logger.warning(f"Missing content_type or content_encoding in {request.message_id=}, assuming defaults")
            request.content_type = self.DEFAULT_CONTENT_TYPE
            request.content_encoding = self.DEFAULT_CONTENT_ENCODING
        
        decoder = self.decoders.get(request.content_type)
        if decoder:
            request.data = decoder.decode(request.raw_data.decode(request.content_encoding))
            return await self.app(request, handler)
        else:
            raise DecodeError(f"Decoding error in '{request.message_id=}', Unsupported {request.content_type}")
