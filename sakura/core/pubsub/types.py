import dataclasses
from abc import abstractmethod
from typing import Callable, Optional

from sakura.core.utils.types import DecoratedCallable


@dataclasses.dataclass
class PubSubRequest:
    raw_data: bytes
    _approve: Callable
    _decline: Callable
    message_headers: dict
    content_encoding: str
    content_type: str
    data: Optional[dict] = None
    message_id: Optional[str] = None
    extra: Optional[dict] = None
    auto_ack: bool = True

    async def approve(self):
        if self.auto_ack:
            raise TypeError("approve() is not supported with auto_ack=True")
        await self._approve()

    async def decline(self):
        if self.auto_ack:
            raise TypeError("decline() is not supported with auto_ack=True")
        await self._decline()


class PubSubApp:
    request: PubSubRequest

    @abstractmethod
    async def __call__(self, request: PubSubRequest, handler: DecoratedCallable):
        raise NotImplementedError
