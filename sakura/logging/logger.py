from __future__ import annotations

from abc import abstractmethod

from sakura.settings import SakuraBaseSettings


class Logger:
    settings: SakuraBaseSettings

    @abstractmethod
    def get_basic_config(self):
        raise NotImplementedError

    @abstractmethod
    def setup(self):
        raise NotImplementedError
