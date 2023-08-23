import asyncio
import functools
import logging
import signal
import threading
import typing
from typing import Callable, Optional

from asyncer import asyncify

from sakura.logging import Logger
from sakura.providers import Provider
from sakura.pubsub.client import PubSubClient
from sakura.utils import merge_dicts
from sakura.utils.decorators import DynamicSelfFunc


class Sakura:
    __providers: dict[str, Provider]
    _once_functions: list[Callable]

    def __init__(
        self,
        providers: Optional[dict[str, Provider]],
        pubsub_clients: Optional[dict[str, PubSubClient]],
        loggers: Optional[list[Logger]] = None,
    ):
        self._once_functions = []
        self.__providers = providers
        self.__pubsub = pubsub_clients
        self.__loggers = loggers
        self.__tasks: list[typing.Coroutine] = []
        self.__should_exit = False
        self.__force_exit = False

    def setup_loggers(self):
        for logger in self.loggers:
            logger.setup()

        config = functools.reduce(
            merge_dicts,
            (a.get_basic_config() for a in self.loggers),
        )
        logging.basicConfig(**config)

    def setup_providers(self):
        for name, provider in self.__providers.items():
            self.__tasks.append(provider.__setup())
            setattr(self, name, provider.__get_dependency())

    def setup_pubsub_clients(self):
        for client_id, client in self.__pubsub.items():
            client.__setup()

    def setup(self):
        self.setup_loggers()
        self.setup_providers()
        self.setup_pubsub_clients()

    async def start(self):
        for pubsub_client in self.__pubsub.values():
            self.__tasks.extend(pubsub_client.__start())

        for func in self._once_functions:
            await DynamicSelfFunc(func)()()

        self.install_signal_handlers()
        await asyncio.gather(*[asyncio.create_task(task) for task in self.__tasks])

    def once(self, orig_func: Callable):
        func = orig_func
        if not asyncio.iscoroutinefunction(func):
            func = asyncify(func)

        self._once_functions.append(func)

        return func

    @property
    def loggers(self):
        return self.__loggers

    @property
    def pubsub(self) -> dict[str, PubSubClient]:
        return self.__pubsub

    def install_signal_handlers(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            # Signals can only be listened to from the main thread.
            return

        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

        for sig in [signal.SIGINT, signal.SIGTERM]:
            loop.add_signal_handler(
                sig, lambda: asyncio.create_task(self.teardown()),
            )

    async def teardown(self) -> None:
        for provider in self.__providers.values():
            await provider.__teardown()

        for pubsub_client in self.__pubsub.values():
            await pubsub_client.__teardown()
