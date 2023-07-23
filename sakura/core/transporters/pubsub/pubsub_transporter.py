import signal
from types import FrameType
from typing import Callable, Any

from sakura.core.exceptions import ClientNotFoundException
from sakura.core.pubsub.client import PubSubClient
from sakura.core.pubsub.subscriber import Subscriber
from sakura.core.pubsub.types import PubSubRequest, PubSubApp
from sakura.core.settings import SakuraBaseSettings, Client
from sakura.core.transporters import Transporter
from sakura.core.transporters.pubsub.middleware import DecodeMiddleware
from sakura.core.transporters.pubsub.middleware.error_handling_middleware import ErrorHandlingMiddleware
from sakura.core.transporters.pubsub.middleware.execute_middleware import ExecuteMiddleware
from sakura.core.utils.factory import client_factory
from sakura.core.utils.types import DecoratedCallable


class PubSubTransporter(PubSubApp, Transporter):
    class Settings(SakuraBaseSettings):
        clients: dict[str, Client]

    __event_store: dict[str, set[tuple[str, Callable[..., Any]]]]
    __clients: dict[str, PubSubClient]

    def __init__(self, settings: Settings):
        self.__settings = settings
        self.__clients = {
            name: client_factory(client.params, client.type, PubSubClient)
            for name, client in self.__settings.clients.items()
        }

        self.__event_store: dict[Subscriber, Callable] = dict()
        self.middleware_stack: Callable = self.build_middleware_stack()

    def build_middleware_stack(self) -> Callable:
        return ErrorHandlingMiddleware(
            app=DecodeMiddleware(
                app=ExecuteMiddleware()
            )
        )

    async def setup(self):
        for name, client in self.__clients.items():
            await client.setup()

    async def generate_tasks(self) -> list[Callable]:
        tasks: list = []

        for subscriber, handler in self.__event_store.items():
            tasks.append(subscriber.consume(
                client=await self.get_client(subscriber.client_id),
                app=self,
                func=handler,
            ))

        return tasks

    def subscribe(self, subscriber: Subscriber) -> Callable[[DecoratedCallable], DecoratedCallable]:
        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self.__event_store[subscriber] = func
            return func

        return decorator

    async def get_client(self, client_id: str) -> PubSubClient:
        client = self.__clients.get(client_id)
        if client is None:
            raise ClientNotFoundException(f"No client with id: '{client_id}'")

        return client

    async def __call__(self, request: PubSubRequest, handler: DecoratedCallable):
        return await self.middleware_stack(request, handler)

    def handle_exit(self, sig: signal.Signals, frame: FrameType) -> None:
        for subscriber, handler in self.__event_store.items():
            subscriber.handle_exit(sig, frame)
