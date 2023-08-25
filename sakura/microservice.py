import asyncio
import inspect
import json
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from dynaconf import Dynaconf

from sakura.logging import Logger
from sakura.providers import Provider
from sakura.pubsub.client import PubSubClient
from sakura.pubsub.factory import pubsub_factory
from sakura.sakura import Sakura
from sakura.settings import Settings
from sakura.utils.decorators import DynamicSelfFunc
from sakura.utils.factory import dict_factory, list_factory

load_dotenv()
logger = logging.getLogger(__name__)


class Microservice(type):
    settings: Settings
    _instance = None
    __sakura_service: Optional[Sakura] = None

    @classmethod
    def __prepare__(cls, name: str, bases: list, **kwargs):
        envvar_prefix = kwargs.get("envvar_prefix", os.getenv("ENVVAR_PREFIX", "SAKURA"))
        settings_files = kwargs.get("settings_files", json.loads(os.getenv("SETTINGS_FILES", '["settings.yaml"]')))
        disable_uvloop = kwargs.get("disable_uvloop", os.getenv("DISABLE_UVLOOP", "False").lower() == "true")

        if not disable_uvloop:
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        else:
            asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

        settings = Dynaconf(
            envvar_prefix=envvar_prefix,
            settings_files=settings_files,
            load_dotenv=True,
        )

        settings = Settings.from_dynaconf(settings)

        pubsub_clients = pubsub_factory(settings.pubsub, PubSubClient)
        providers = dict_factory(settings.providers, Provider)
        loggers = list_factory(settings.loggers, Logger)

        cls.__sakura_service = Sakura(providers=providers, pubsub_clients=pubsub_clients, loggers=loggers)
        sakura = cls.__sakura_service

        sakura.setup()

        return {
            "__sakura_service": sakura,
            "once": sakura.once,
            "pubsub": sakura.pubsub,
            "config": settings.config, **{
                name: sakura.__getattribute__(name) for name, member in inspect.getmembers(sakura)
                if not inspect.ismethod(member) and not name.startswith("_")
            },
        }

    def __new__(cls, name, bases, attrs, **kwargs):  # noqa: ARG003
        if not cls._instance:
            cls._instance = super().__new__(cls, name, bases, attrs)()
            DynamicSelfFunc._instance = cls._instance
        loop = asyncio.get_event_loop()

        try:
            loop.run_until_complete(cls.__sakura_service.start())
        except KeyboardInterrupt:
            logger.error("Service has been closed unexpectedly")
        finally:
            loop.run_until_complete(cls.__sakura_service.teardown())

        return cls._instance
