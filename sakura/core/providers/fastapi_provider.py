import asyncio
import logging
import signal
import typing
from typing import Optional, Any

import fastapi
import pydantic
import uvicorn
from uvicorn import Config, Server

from sakura.core.logging.loguru import InterceptHandler
from sakura.core.providers import Provider
from sakura.core.settings import SakuraBaseSettings


# noinspection DuplicatedCode
class FastAPIProvider(Provider):
    server: Optional[Server] = None

    class Settings(SakuraBaseSettings):
        extra: dict = pydantic.Field(default_factory=dict)
        port: int = "8080"
        title: str = "FastAPI"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.app = fastapi.FastAPI(
            title=settings.title,
            **settings.extra,
        )

    def setup(self) -> typing.Coroutine:
        # noinspection PyTypeChecker
        config = Config(
            self.app,
            host='0.0.0.0',
            port=self.settings.port,
        )

        self.server = Server(config=config)
        logging.getLogger("uvicorn").removeHandler(logging.getLogger("uvicorn").handlers[0])
        logging.getLogger("uvicorn.access").removeHandler(logging.getLogger("uvicorn.access").handlers[0])

        logging.getLogger("uvicorn").addHandler(InterceptHandler())
        logging.getLogger("uvicorn.access").addHandler(InterceptHandler())

        # Remove uvicorn signal handling
        uvicorn.server.HANDLED_SIGNALS = tuple()

        return self.server.serve()

    async def teardown(self):
        self.server.handle_exit(sig=signal.SIGINT, frame=None)

    def get_dependency(self) -> Any:
        return self.app
