import logging
import typing

import pydantic

from sakura.providers.provider import Provider
from sakura.providers.rabbitmq_provider.rabbitmq_client import RabbitMQClient
from sakura.providers.rabbitmq_provider.rabbitmq_client.types import Exchange, Queue
from sakura.settings.settings import SakuraBaseSettings

logger = logging.getLogger(__name__)


class RabbitMQProviderSettings(SakuraBaseSettings):
        class DeclareOptions(pydantic.BaseModel):
            queues: list[Queue]
            exchanges: list[Exchange]

        uri: str = "amqp://localhost:5672"
        encoding: str = "utf-8"
        content_type: str = "application/json"
        virtual_host: str = "/"

        declare: DeclareOptions = pydantic.Field(default_factory=DeclareOptions)

class RabbitMQProvider(Provider):
    Settings = RabbitMQProviderSettings

    def __init__(self, settings: Settings):
        self.settings = settings
        self.__rabbitmq_client = RabbitMQClient(
            uri=settings.uri,
            virtual_host=settings.virtual_host,
            encoding=settings.encoding,
            content_type=settings.content_type,
        )

    def _setup(self) -> typing.Coroutine:
        async def setup_resources():
            await self.__rabbitmq_client.setup()

            for exchange in self.settings.declare.exchanges:
                if exchange.name:
                    await self.__rabbitmq_client.get_exchange(exchange)

            for queue in self.settings.declare.queues:
                await self.__rabbitmq_client.get_queue(queue, declare=True)

        return setup_resources()

    async def _teardown(self):
        self.__rabbitmq_client.close()

    def _get_dependency(self) -> RabbitMQClient:
        return self.__rabbitmq_client
