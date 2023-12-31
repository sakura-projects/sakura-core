import asyncio
import inspect
from typing import Optional

from dynaconf import Dynaconf

from sakura.logging import Logger
from sakura.providers import Provider
from sakura.sakura import Sakura
from sakura.settings import Settings
from sakura.utils.decorators import DynamicSelfFunc
from sakura.utils.factory import dict_factory, list_factory


class Microservice(type):
    settings: Settings
    _instance = None
    __sakura_service: Optional[Sakura] = None

    @classmethod
    def __prepare__(cls, name: str, bases: list, **kwargs):
        envvar_prefix = kwargs.get("envvar_prefix", "SAKURA")
        settings_files = kwargs.get("settings_files", ["settings.yaml"])
        load_dotenv = kwargs.get("load_dotenv", False)
        disable_uvloop = kwargs.get("disable_uvloop", False)

        if not disable_uvloop:
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        else:
            asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

        settings = Dynaconf(
            envvar_prefix=envvar_prefix,
            settings_files=settings_files,
            load_dotenv=load_dotenv,
        )

        settings = Settings.from_dynaconf(settings)

        providers = dict_factory(settings.providers, Provider)
        loggers = list_factory(settings.loggers, Logger)

        cls.__sakura_service = Sakura(providers=providers, loggers=loggers)
        sakura = cls.__sakura_service

        sakura.setup()

        return {
            "__sakura_service": sakura,
            "once": sakura.once,
            "config": settings.config, **{
                name: sakura.__getattribute__(name) for name, member in inspect.getmembers(sakura)
                if not inspect.ismethod(member) and not name.startswith("_")
            },
        }

    def __new__(cls, name, bases, attrs, **kwargs):  # noqa: ARG003
        if not cls._instance:
            cls._instance = super().__new__(cls, name, bases, attrs)
            DynamicSelfFunc._instance = cls._instance

        asyncio.run(cls.__sakura_service.start())
        return cls._instance
