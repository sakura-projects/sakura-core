import signal
from abc import abstractmethod
from types import FrameType


class HTTPClient:
    @abstractmethod
    async def serve(self):
        raise NotImplementedError

    @abstractmethod
    def handle_exit(self, sig: signal.Signals, frame: FrameType) -> None:
        raise NotImplementedError
