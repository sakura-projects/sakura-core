from typing import Union

import pydantic.fields
from dynaconf import LazySettings
from dynaconf.utils.boxing import DynaBox
from pydantic import BaseModel


class SakuraBaseSettings(BaseModel):
    @classmethod
    def from_dynaconf(cls, raw_settings: Union[LazySettings, dict]):
        if isinstance(raw_settings, LazySettings):
            raw_settings = {k.lower(): v for k, v in raw_settings.items()}

        return cls(**raw_settings)


class Client(SakuraBaseSettings):
    type: str
    params: dict


class Settings(SakuraBaseSettings):
    loggers: DynaBox
    transporters: DynaBox = pydantic.fields.Field(default_factory=DynaBox)
    providers: DynaBox = pydantic.fields.Field(default_factory=DynaBox)
    config: DynaBox = pydantic.fields.Field(default_factory=DynaBox)
