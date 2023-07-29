import signal
from abc import abstractmethod
from typing import Any, Callable

from sakura.pubsub.client import PubSubClient
from sakura.pubsub.types import PubSubApp


class Subscriber:
    client_id: Any
    should_exit: bool = False
    force_exit: bool = False

    async def consume(self, client: PubSubClient, app: PubSubApp, func: Callable) -> None:
        await self.startup(client, app, func)
        if self.should_exit:
            return
        await self.main_loop(client, app, func)
        await self.shutdown(client, app, func)

    @abstractmethod
    async def startup(self, client: PubSubClient, app: PubSubApp, func: Callable) -> None:
        raise NotImplementedError

    @abstractmethod
    async def main_loop(self, client: PubSubClient, app: PubSubApp, func: Callable) -> None:
        raise NotImplementedError

    @abstractmethod
    async def shutdown(self, client: PubSubClient, app: PubSubApp, func: Callable) -> None:
        raise NotImplementedError

    @abstractmethod
    async def create_callback(self, client: PubSubClient, app: PubSubApp, func: Callable) -> None:
        raise NotImplementedError

    def handle_exit(self, sig: signal.Signals) -> None:
        if self.should_exit and sig == signal.SIGINT:
            self.force_exit = True
        else:
            self.should_exit = True
