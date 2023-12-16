import functools
import logging
import signal
import typing
from typing import Any, Optional

import pydantic

from sakura.logging.loguru import InterceptHandler
from sakura.providers import Provider
from sakura.settings import SakuraBaseSettings
from sakura.utils.decorators import DynamicSelfFunc

logger = logging.getLogger(__name__)


try:
    import fastapi
    import uvicorn
except ImportError as e:
    logger.error("Make sure that http dependencies are installed.", exc_info=e)
    raise e


class FastAPIProvider(Provider):
    server: Optional[uvicorn.Server] = None

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

        def deco(func):
            def wildcard_method(*args, **kwargs):
                result = func(*args, **kwargs)
                return lambda f: result(DynamicSelfFunc(f)())

            return functools.wraps(func)(wildcard_method)

        for method in ["get", "post", "put", "delete"]:
            self.app.__setattr__(method, deco(self.app.__getattribute__(method)))

    def setup(self) -> typing.Coroutine:
        # TODO: make sure that Config is running on the same event loop as the other services
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",  # noqa: S104
            port=self.settings.port,
        )

        self.server = uvicorn.Server(config=config)
        logging.getLogger("uvicorn").removeHandler(logging.getLogger("uvicorn").handlers[0])
        logging.getLogger("uvicorn.access").removeHandler(logging.getLogger("uvicorn.access").handlers[0])

        logging.getLogger("uvicorn").addHandler(InterceptHandler())
        logging.getLogger("uvicorn.access").addHandler(InterceptHandler())

        # Remove uvicorn signal handling
        uvicorn.server.HANDLED_SIGNALS = ()

        logger.info("Starting fastapi_provider server")

        return self.server.serve()

    async def teardown(self):
        self.server.handle_exit(sig=signal.SIGINT, frame=None)

    def get_dependency(self) -> Any:
        return self.app
