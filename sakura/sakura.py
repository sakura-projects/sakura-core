import asyncio
import functools
import logging
import signal
import threading
import typing

from typing import Optional, Callable

from asyncer import asyncify

from sakura.logging import Logger
from sakura.providers import Provider
from sakura.utils import merge_dicts
from sakura.utils.decorators import DynamicSelfFunc


class Sakura:
    __providers: dict[str, Provider]
    _once_functions: list[Callable]

    def __init__(
        self,
        providers: Optional[dict[str, Provider]],
        loggers: Optional[list[Logger]] = None,
    ):
        self._once_functions = []
        self.__providers = providers
        self.__loggers = loggers
        self.__tasks: list[typing.Coroutine] = []
        self.__should_exit = False
        self.__force_exit = False
        self.init_logging()

    def init_logging(self):
        for logger in self.loggers:
            logger.setup()

        config = functools.reduce(merge_dicts, map(lambda a: a.get_basic_config(), self.loggers))
        logging.basicConfig(**config)

    def setup_providers(self):
        for name, provider in self.__providers.items():
            self.__tasks.append(provider.setup())
            setattr(self, name, provider.get_dependency())

    def setup(self):
        self.setup_providers()

    async def start(self):
        for func in self._once_functions:
            await DynamicSelfFunc(func)()()

        self.install_signal_handlers()
        await asyncio.gather(*[asyncio.create_task(task) for task in self.__tasks])

        for provider in self.__providers.values():
            await provider.teardown()

    def once(self, orig_func: Callable):
        func = orig_func
        if not asyncio.iscoroutinefunction(func):
            func = asyncify(func)

        self._once_functions.append(func)

        return func

    @property
    def loggers(self):
        return self.__loggers

    def install_signal_handlers(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            # Signals can only be listened to from the main thread.
            return

        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

        for sig in [signal.SIGINT, signal.SIGTERM]:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.teardown(sig)))

    async def teardown(self, sig: signal.Signals) -> None:
        if self.__should_exit and sig == signal.SIGINT:
            self.__force_exit = True
        else:
            self.__should_exit = True

        for provider in self.__providers.values():
            await provider.teardown()
