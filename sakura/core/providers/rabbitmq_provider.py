import asyncio
from typing import Any

from sakura.core.providers import Provider
from sakura.core.rabbitmq import RabbitMQClient
from sakura.core.settings import SakuraBaseSettings
from sakura.core.utils.factory import client_factory


class ClientSettings(SakuraBaseSettings):
    type: str
    params: dict


class RabbitMQProvider(Provider):
    class Settings(SakuraBaseSettings):
        client: ClientSettings

    def __init__(self, settings: Settings):
        self.settings = settings
        self.__client: RabbitMQClient = client_factory(
            self.settings.client.params,
            self.settings.client.type,
            RabbitMQClient,
        )

        self.is_open = False

    async def setup(self) -> asyncio.Task:
        return asyncio.create_task(self.__client.setup())

    async def teardown(self):
        return self.__client.close()

    def get_dependency(self) -> Any:
        return self.__client
