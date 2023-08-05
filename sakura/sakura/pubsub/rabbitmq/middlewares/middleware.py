import abc
from typing import Callable


class Middleware(abc.ABC):
    @abc.abstractmethod
    def __call__(self, func: Callable) -> Callable:
        raise NotImplementedError
