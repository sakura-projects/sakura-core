import typing
from abc import abstractmethod


class Provider:
    def setup(self) -> typing.Coroutine:
        pass

    async def teardown(self):
        pass

    @abstractmethod
    def get_dependency(self) -> typing.Any:
        raise NotImplementedError
