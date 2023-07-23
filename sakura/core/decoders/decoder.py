from abc import abstractmethod


class Decoder:
    @abstractmethod
    def decode(self, body: bytes) -> dict:
        raise NotImplementedError
