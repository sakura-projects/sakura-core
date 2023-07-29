import typing
from typing import Any

from sakura.providers import Provider
from sakura.rabbitmq import RabbitMQClient
from sakura.settings import SakuraBaseSettings
from sakura.utils.factory import client_factory


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

    def setup(self) -> typing.Coroutine:
        return self.__client.setup()

    async def teardown(self):
        return self.__client.close()

    def get_dependency(self) -> Any:
        return self.__client
