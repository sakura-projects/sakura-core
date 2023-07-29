from __future__ import annotations
import inspect
import asyncio
import functools
import logging
import signal
import threading
import typing

from types import FrameType
from typing import Optional, Callable, TypeVar

from asyncer import asyncify
from dynaconf import Dynaconf

from sakura.core.logging import Logger
from sakura.core.providers import Provider
from sakura.core.settings import Settings
from sakura.core.transporters.transporter import Transporter
from sakura.core.utils import merge_dicts
from sakura.core.utils.decorators import DynamicSelfFunc
from sakura.core.utils.factory import list_factory, dict_factory

HANDLED_SIGNALS = (
    signal.SIGINT,
    signal.SIGTERM,
)


T = TypeVar("T")


class Sakura:
    __transporters: list[Transporter]
    __providers: dict[str, Provider]
    _once_functions: list[Callable]

    def __init__(
        self,
        transporters: Optional[list[Transporter]],
        providers: Optional[dict[str, Provider]],
        loggers: Optional[list[Logger]] = None,
    ):
        self._once_functions = []
        self.__transporters = transporters
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

    async def setup_transporters(self):
        for transporter in self.__transporters:
            await transporter.setup()

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

        for transporter in self.__transporters:
            await transporter.teardown()

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

        try:
            for sig in HANDLED_SIGNALS:
                loop.add_signal_handler(sig, self.handle_exit, sig, None)
        except NotImplementedError: # pragma: no cover
            # Windows
            for sig in HANDLED_SIGNALS:
                signal.signal(sig, self.handle_exit)

    def handle_exit(self, sig: signal.Signals, frame: FrameType) -> None:
        if self.__should_exit and sig == signal.SIGINT:
            self.__force_exit = True
        else:
            self.__should_exit = True
        
        for transporter in self.__transporters:
            transporter.handle_exit(sig, frame)


# class Microservice(Sakura):
#     settings: Settings
#     _instance: Any = None
#     ___microservice_instance: Microservice = None
#
#     def __new__(cls, *args, **kwargs):
#         if not cls.___microservice_instance:
#             cls.___microservice_instance = super().__new__(cls)
#         return cls.___microservice_instance
#
#     def __init__(self):
#         transporters = list_factory(self.settings.transporters, Transporter)
#         providers = dict_factory(self.settings.providers, Provider)
#         loggers = list_factory(self.settings.loggers, Logger)
#         super(Microservice, self).__init__(transporters, providers, loggers)
#
#     def __call__(self) -> Callable[[Type[T]], Type[T]]:
#         def decorator(class_: Type[T]) -> Type[T]:
#             orig_new = class_.__new__
#
#             def _new_(cls, *args, **kwargs):
#                 if self._instance is None:
#                     instance = orig_new(cls, *args, **kwargs)
#                     self._instance = instance
#                     class_._instance = instance
#
#                 return self._instance
#
#             class_.__new__ = _new_
#
#             class_.sakura_service = True
#             return class_
#
#         return decorator


class Microservice(type):
    settings: Settings
    _instance = None
    __sakura_service: Optional[Sakura] = None

    @classmethod
    def __prepare__(mcs, name: str, bases: list, **kwargs):
        envvar_prefix = kwargs.get('envvar_prefix', 'SAKURA')
        settings_files = kwargs.get('settings_files', ['settings.yaml'])
        load_dotenv = kwargs.get('load_dotenv', False)

        settings = Dynaconf(
            envvar_prefix=envvar_prefix,
            settings_files=settings_files,
            load_dotenv=load_dotenv,
        )

        settings = Settings.from_dynaconf(settings)

        transporters = list_factory(settings.transporters, Transporter)
        providers = dict_factory(settings.providers, Provider)
        loggers = list_factory(settings.loggers, Logger)

        mcs.__sakura_service = Sakura(transporters=transporters, providers=providers, loggers=loggers)
        sakura = mcs.__sakura_service

        sakura.setup()

        return {
            '__sakura_service': sakura,
            'once': sakura.once,
            'config': settings.config, **{
                name: sakura.__getattribute__(name) for name, member in inspect.getmembers(sakura)
                if not inspect.ismethod(member) and not name.startswith('_')
            }
        }

    def __new__(mcs, name, bases, attrs, **kwargs):
        if not mcs._instance:
            mcs._instance = super(Microservice, mcs).__new__(mcs, name, bases, attrs)
            DynamicSelfFunc._instance = mcs._instance

        asyncio.run(mcs.__sakura_service.start())
        return mcs._instance
