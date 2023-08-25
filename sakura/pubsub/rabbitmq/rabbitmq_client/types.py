import dataclasses
from enum import Enum
from typing import Callable, Optional


class Headers(Enum):
    REDELIVERED_COUNT = "x-redelivered-count"


class DeliveryMode(Enum):
    TRANSIENT_DELIVERY_MODE = "transient"
    PERSISTENT_DELIVERY_MODE = "persistent"


@dataclasses.dataclass(eq=True, frozen=True)
class Exchange:
    name: str = "default"
    arguments: dict = dataclasses.field(default_factory=dict)
    type: str = "direct"  # noqa: A003
    durable: bool = True
    auto_delete: bool = False
    delivery_mode: DeliveryMode = DeliveryMode.TRANSIENT_DELIVERY_MODE


@dataclasses.dataclass(eq=True, frozen=True)
class Queue:
    name: str
    arguments: dict = dataclasses.field(default_factory=dict)
    binding_arguments: dict = dataclasses.field(default_factory=dict)
    consumer_arguments: dict = dataclasses.field(default_factory=dict)
    on_declared: Optional[Callable] = None
    exchange: Optional[Exchange] = None
    routing_key: Optional[str] = None
    durable: bool = True
    auto_delete: bool = False
    exclusive: bool = False
    expires: float = 0


@dataclasses.dataclass
class PublishAddress:
    """
    Describes the needed params to publish a message
    """
    exchange: Exchange
    routing_key: str
