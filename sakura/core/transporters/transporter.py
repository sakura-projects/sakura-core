import signal
from abc import abstractmethod
from types import FrameType


class Transporter:
    @abstractmethod
    async def generate_tasks(self) -> list:
        raise NotImplementedError

    async def setup(self):
        pass

    async def teardown(self):
        pass

    @abstractmethod
    def handle_exit(self, sig: signal.Signals, frame: FrameType) -> None:
        raise NotImplementedError
