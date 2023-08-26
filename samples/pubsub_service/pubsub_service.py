import functools
import logging
import typing
from typing import Callable

from sakura.microservice import Microservice
from sakura.pubsub.client import PubSubClient
from sakura.pubsub.middlewares import Middleware

logger = logging.getLogger(__name__)


class UserMiddleware(Middleware):
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger.info("from user middleware")
            return await func(*args, **kwargs)

        return wrapper


class Service(metaclass=Microservice, settings_files=["samples/pubsub_service/settings.yaml"], disable_uvloop=True):
    once: Callable
    pubsub: dict[str, PubSubClient]
    config: dict

    def hello(self):
        logger.info("hellloo")

    @once
    async def run(self):
        logger.info("Started service")
        self.hello()

    @pubsub["client1"].subscribe("subscriber1", middlewares=[UserMiddleware()])
    def get_from_rabbit(self, foo: str):  # noqa: ARG002
        logger.info("From rabbit...")

        return "hello"
