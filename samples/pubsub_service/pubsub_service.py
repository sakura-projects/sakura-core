import logging
from typing import Callable

from sakura.microservice import Microservice
from sakura.pubsub.client import PubSubClient

logger = logging.getLogger(__name__)


class Service(metaclass=Microservice, settings_files=["samples/pubsub_service/settings.yaml"], disable_uvloop=True):
    once: Callable
    pubsub: dict[str, PubSubClient]
    config: dict

    @once
    async def run(self):
        logger.info("Started service")

    @pubsub["client1"].subscribe("subscriber1")
    def get_from_rabbit(self, *args, **kwargs):
        logger.info("From rabbit...")
