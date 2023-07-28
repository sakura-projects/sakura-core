from abc import abstractmethod
from asyncio import Task
from typing import Any


class Provider:
    async def setup(self) -> Task:
        pass

    async def teardown(self):
        pass

    @abstractmethod
    def get_dependency(self) -> Any:
        raise NotImplementedError
