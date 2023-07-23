import logging
import os.path

import aio_pika.exceptions

from sakura.core.pubsub.types import PubSubRequest, PubSubApp
from sakura.core.utils.types import DecoratedCallable

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(PubSubApp):
    def __init__(self, app: PubSubApp):
        self.app = app

    async def __call__(self, request: PubSubRequest, handler: DecoratedCallable):
        try:
            res = await self.app(request, handler)
            if request.auto_ack:
                await request._approve()
            return res
        except Exception as e:
            tb = e.__traceback__
            while tb.tb_next:
                tb = tb.tb_next
            module = os.path.splitext(os.path.relpath(tb.tb_frame.f_code.co_filename, os.getcwd()))[0].replace('/', '.')
            logger.error(f"Error in '{module}.{tb.tb_frame.f_code.co_name}:{tb.tb_frame.f_lineno}': "
                         f"{type(e).__name__}: {e}")
            
            try:
                await request._decline()
            except aio_pika.exceptions.MessageProcessError:
                logger.error("Message already declined")
