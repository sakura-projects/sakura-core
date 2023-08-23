import typing
from abc import abstractmethod


class Provider:
    def __setup(self) -> typing.Coroutine:
        pass

    async def __teardown(self):
        pass

    @abstractmethod
    def __get_dependency(self) -> typing.Any:
        raise NotImplementedError
