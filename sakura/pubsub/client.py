import functools
from abc import abstractmethod
from typing import Callable

from sakura.pubsub.middlewares import Middleware


class PubSubClient:
    _event_store: dict[str, tuple[Callable, list[Middleware]]] = {}

    @abstractmethod
    def _setup(self):
        raise NotImplementedError

    @abstractmethod
    def _start(self):
        raise NotImplementedError

    @abstractmethod
    async def _teardown(self):
        raise NotImplementedError

    def subscribe(self, subscriber_id: str, middlewares: list[Middleware] = None) -> Callable:
        def decorator(func: Callable) -> Callable:
            self._event_store[subscriber_id] = (func, middlewares)

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator
