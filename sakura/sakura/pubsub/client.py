import functools
from abc import abstractmethod
from typing import Callable


class PubSubClient:
    _event_store: dict[str, Callable] = {}

    @abstractmethod
    def __setup(self):
        raise NotImplementedError

    @abstractmethod
    def __start(self):
        raise NotImplementedError

    @abstractmethod
    async def __teardown(self):
        raise NotImplementedError

    def subscribe(self, subscriber_id: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            self._event_store[subscriber_id] = func

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator
