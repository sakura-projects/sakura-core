from abc import abstractmethod
from typing import Any


class Provider:
    async def setup(self):
        pass

    async def teardown(self):
        pass

    @abstractmethod
    async def get_dependency(self) -> Any:
        raise NotImplementedError
