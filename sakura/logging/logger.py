from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sakura.settings import SakuraBaseSettings


class Logger:
    settings: SakuraBaseSettings

    @abstractmethod
    def get_basic_config(self):
        raise NotImplementedError

    @abstractmethod
    def setup(self):
        raise NotImplementedError
