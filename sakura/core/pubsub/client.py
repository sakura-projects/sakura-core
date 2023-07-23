from abc import abstractmethod


class PubSubClient:
    @abstractmethod
    def setup(self):
        raise NotImplementedError
