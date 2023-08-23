from sakura.pubsub.settings import Settings as PubSubSettings
from sakura.settings import SakuraBaseSettings


class SubscriberSettings(SakuraBaseSettings):
    queue: str
    auto_ack: bool = True
    prefetch_count: int = 5
    retry_interval: int = 5


class PublisherSettings(SakuraBaseSettings):
    exchange: str
    routing_key: str


class Settings(PubSubSettings):
    params: dict
    subscribers: dict[str, SubscriberSettings]
    publishers: dict[str, PublisherSettings]
