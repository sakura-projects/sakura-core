import asyncio
from collections.abc import Coroutine

from sakura.exceptions import SubscriberNotFoundError
from sakura.providers.rabbitmq_provider.provider import RabbitMQProvider
from sakura.pubsub.client import PubSubClient
from sakura.pubsub.rabbitmq.settings import Settings
from sakura.pubsub.rabbitmq.subscriber import RabbitMQSubscriber


class RabbitMQPubSubClient(PubSubClient):
    Settings = Settings
    __running_subscribers: dict[str, RabbitMQSubscriber] = {}

    def __init__(self, settings: Settings):
        self.serialization = settings.serialization
        self.subscribers = settings.subscribers
        self.publishers = settings.publishers

        self.__rabbitmq_provider = RabbitMQProvider(settings=settings.params)

    def _setup(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__rabbitmq_provider._setup())

    def _start(self) -> list[Coroutine]:
        tasks: list[Coroutine] = []

        for subscriber_id, (func, middlewares) in self._event_store.items():
            if subscriber_id not in self.subscribers:
                raise SubscriberNotFoundError

            subscriber = RabbitMQSubscriber(
                subscriber_id=subscriber_id,
                func=func,
                middlewares=middlewares,
                settings=self.subscribers[subscriber_id],
                client=self.__rabbitmq_provider._get_dependency(),
            )

            self.__running_subscribers[subscriber_id] = subscriber

            tasks.append(subscriber.run())

        return tasks

    async def _teardown(self):
        for subscriber in self.__running_subscribers.values():
            subscriber.should_exit = True
