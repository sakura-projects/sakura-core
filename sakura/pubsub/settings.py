import pydantic

from sakura.settings import SakuraBaseSettings


class Settings(SakuraBaseSettings):
    params: dict
    subscribers: dict[str, pydantic.BaseModel]
    publishers: dict[str, pydantic.BaseModel]
    serialization: str
