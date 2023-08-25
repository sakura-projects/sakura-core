import pydantic

from sakura.pubsub.rabbitmq.rabbitmq_client.types import Exchange, Queue
from sakura.settings import SakuraBaseSettings


class Declare(SakuraBaseSettings):
    queues: list[Queue] = pydantic.Field(default_factory=list)
    exchanges: list[Exchange] = pydantic.Field(default_factory=list)


class RabbitMQClientSettings(SakuraBaseSettings):
    declare: Declare = pydantic.Field(default_factory=Declare)
    uri: str = "amqp://localhost:5672"
    virtualhost: str = "/"
    encoding: str = "utf-8"
    content_type: str = "application/json"
