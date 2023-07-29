import logging
import sys
from typing import Any, Optional

from loguru import logger

# noinspection PyProtectedMember
from loguru._defaults import LOGURU_FORMAT

from sakura.logging import Logger
from sakura.settings import SakuraBaseSettings


class LevelConfig(SakuraBaseSettings):
    name: str
    no: int
    color: str
    icon: str


class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentation.
    See https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where orinated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class Loguru(Logger):
    class Settings(SakuraBaseSettings):
        handlers: list[dict[str, Any]]
        levels: Optional[list[LevelConfig]] = None
        extra: Optional[dict[Any, Any]] = None
        serialize: bool = True

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    def setup(self):
        config = self.settings.dict()
        config["handlers"].append(
            {
                "sink": sys.stdout,
                "format": LOGURU_FORMAT,
                "serialize": bool(config.pop("serialize")),
            }
        )
        logger.configure(**config)

    def get_basic_config(self) -> dict:
        return {"handlers": [InterceptHandler()], "level": logging.INFO}
