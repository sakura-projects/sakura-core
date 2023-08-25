import logging

import pydantic

from sakura.providers.provider import Provider
from sakura.providers.rabbitmq_provider.rabbitmq_client.client import RabbitMQClient
from sakura.providers.rabbitmq_provider.rabbitmq_client.types import Exchange, Queue
from sakura.settings.settings import SakuraBaseSettings

logger = logging.getLogger(__name__)


class RabbitMQProvider(Provider):
    class Settings(SakuraBaseSettings):
        class DeclareOptions(pydantic.BaseModel):
            queues: list[Queue]
            exchanges: list[Exchange]

        uri: str = "amqp://localhost:5672"
        encoding: str = "utf-8"
        content_type: str = "application/json"
        virtual_host: str = "/"

        declare: DeclareOptions = pydantic.Field(default_factory=DeclareOptions)


    def __init__(self, settings: Settings):
        self.settings = settings
        self.__rabbitmq_client = RabbitMQClient()

        def deco(func):
            def wildcard_method(*args, **kwargs):
                result = func(*args, **kwargs)
                return lambda f: result(DynamicSelfFunc(f)())

            return functools.wraps(func)(wildcard_method)

        for method in ["get", "post", "put", "delete"]:
            self.app.__setattr__(method, deco(self.app.__getattribute__(method)))

    def _setup(self) -> typing.Coroutine:
        # TODO: make sure that Config is running on the same event loop as the other services
        config = Config(
            self.app,
            host="0.0.0.0",  # noqa: S104
            port=self.settings.port,
        )

        self.server = Server(config=config)
        logging.getLogger("uvicorn").removeHandler(logging.getLogger("uvicorn").handlers[0])
        logging.getLogger("uvicorn.access").removeHandler(logging.getLogger("uvicorn.access").handlers[0])

        logging.getLogger("uvicorn").addHandler(InterceptHandler())
        logging.getLogger("uvicorn.access").addHandler(InterceptHandler())

        # Remove uvicorn signal handling
        uvicorn.server.HANDLED_SIGNALS = ()

        logger.info("Starting fastapi_provider server")

        return self.server.serve()

    async def _teardown(self):
        self.server.handle_exit(sig=signal.SIGINT, frame=None)

    def _get_dependency(self) -> Any:
        return self.app
