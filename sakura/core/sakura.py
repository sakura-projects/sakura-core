import asyncio
import functools
import logging
import signal
import threading

from types import FrameType
from typing import Optional, Any, Callable

from asyncer import asyncify

from sakura.core.exceptions import HTTPTransporterNotInitialized, PubSubTransporterNotInitialized
from sakura.core.logging import Logger
from sakura.core.providers import Provider
from sakura.core.transporters.transporter import Transporter
from sakura.core.transporters.http.http_transporter import HTTPTransporter
from sakura.core.transporters.pubsub.pubsub_transporter import PubSubTransporter
from sakura.core.utils import merge_dicts

HANDLED_SIGNALS = (
    signal.SIGINT,
    signal.SIGTERM,
)


class Sakura:
    _transporters: list[Transporter]
    _providers: dict[str, Provider]
    _once_functions: list[Callable]

    def __init__(
        self,
        transporters: Optional[list[Transporter]],
        providers: Optional[dict[str, Provider]],
        loggers: Optional[list[Logger]] = None,
    ):
        self._once_functions = []
        self._transporters = transporters
        self._providers = providers
        self.__loggers = loggers
        self.should_exit = False
        self.force_exit = False
        self.init_logging()

    def init_logging(self):
        for logger in self.loggers:
            logger.setup()

        config = functools.reduce(merge_dicts, map(lambda a: a.get_basic_config(), self.loggers))
        logging.basicConfig(**config)

    async def setup_transporters(self):
        for transporter in self._transporters:
            await transporter.setup()

    async def setup_providers(self):
        for provider in self._providers.values():
            await provider.setup()

    async def setup(self):
        await self.setup_transporters()
        await self.setup_providers()

    async def start(self):
        tasks: list = []
        loop = asyncio.get_running_loop()

        for transporter in self._transporters:
            transporter_tasks = await transporter.generate_tasks()

            for task in transporter_tasks:
                tasks.append(loop.create_task(task))

        self.install_signal_handlers()
        await asyncio.gather(*tasks, loop=loop)

    @property
    def http(self):
        for transporter in self._transporters:
            if isinstance(transporter, HTTPTransporter):
                return transporter.http

        raise HTTPTransporterNotInitialized()

    @property
    def pubusub(self):
        for transporter in self._transporters:
            if isinstance(transporter, PubSubTransporter):
                return transporter

        raise PubSubTransporterNotInitialized()

    def once(self, orig_func):
        func = orig_func
        if not asyncio.iscoroutinefunction(func):
            func = asyncify(func)

        self._once_functions.append(func)

        return func

    @property
    def loggers(self):
        return self.__loggers

    async def providers(self, provider_name: str) -> Any:
        return await self._providers[provider_name].get_dependency()

    def install_signal_handlers(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            # SIgnals can only be listened to from the main thread.
            return

        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

        try:
            for sig in HANDLED_SIGNALS:
                loop.add_signal_handler(sig, self.handle_exit, sig, None)
        except NotImplementedError: # pragma: no cover
            # Windows
            for sig in HANDLED_SIGNALS:
                signal.signal(sig, self.handle_exit)

    def handle_exit(self, sig: signal.Signals, frame: FrameType) -> None:
        if self.should_exit and sig == signal.SIGINT:
            self.force_exit = True
        else:
            self.should_exit = True
        
        for transporter in self._transporters:
            transporter.handle_exit(sig, frame)
