import asyncio
from collections.abc import Coroutine

from sakura.exceptions import SubscriberNotFoundError
from sakura.pubsub.client import PubSubClient
from sakura.pubsub.rabbitmq.rabbitmq_client import RabbitMQClient
from sakura.pubsub.rabbitmq.rabbitmq_client import Settings as RabbitMQClientSettings
from sakura.pubsub.rabbitmq.settings import Settings
from sakura.pubsub.rabbitmq.subsriber import RabbitMQSubscriber


class RabbitMQPubSubClient(PubSubClient):
    Settings = Settings
    __running_subscribers: dict[str, RabbitMQSubscriber] = {}

    def __init__(self, settings: Settings):
        self.__settings = settings
        self.serialization = settings.serialization
        self.subscribers = settings.subscribers
        self.publishers = settings.publishers

        self.__rabbitmq_client = RabbitMQClient(RabbitMQClientSettings.from_dynaconf(raw_settings=settings.params))
        super().__init__()

    def setup(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__rabbitmq_client.setup())

    def start(self) -> list[Coroutine]:
        tasks: list[Coroutine] = []

        for subscriber_id, func in self._event_store.items():
            if subscriber_id not in self.subscribers:
                raise SubscriberNotFoundError

            subscriber = RabbitMQSubscriber(
                settings=self.subscribers[subscriber_id],
                client=self.__rabbitmq_client,
                func=func,
                subscriber_id=subscriber_id,
            )

            self.__running_subscribers[subscriber_id] = subscriber

            tasks.append(subscriber.run())

        return tasks

    async def teardown(self):
        for subscriber_id, subscriber in self.__running_subscribers.items():
            subscriber.should_exit = True
