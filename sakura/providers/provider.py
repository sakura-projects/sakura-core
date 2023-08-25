import typing
from abc import abstractmethod


class Provider:
    def _setup(self) -> typing.Coroutine:
        pass

    async def _teardown(self):
        pass

    @abstractmethod
    def _get_dependency(self) -> typing.Any:
        raise NotImplementedError
