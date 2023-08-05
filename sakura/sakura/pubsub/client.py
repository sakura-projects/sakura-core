import functools
from abc import abstractmethod
from typing import Callable


class PubSubClient:
    _event_store: dict[str, Callable] = {}

    @abstractmethod
    def setup(self):
        raise NotImplementedError

    @abstractmethod
    def start(self):
        raise NotImplementedError

    @abstractmethod
    async def teardown(self):
        raise NotImplementedError

    def subscribe(self, subscriber_id: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            self._event_store[subscriber_id] = func
            return func

        return decorator
