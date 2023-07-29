import asyncio
import logging
from typing import Callable, Optional

from aio_pika.abc import AbstractIncomingMessage

from sakura.pubsub import Subscriber
from sakura.pubsub.client import PubSubClient
from sakura.pubsub.types import PubSubApp, PubSubRequest
from sakura.rabbitmq import RabbitMQClient
from sakura.rabbitmq.types import PublishAddress, Queue

logger = logging.getLogger(__name__)


class RabbitMQSubscriber(Subscriber):
    def __init__(  # noqa: PLR0913
        self,
        client_id: str,
        queue: Optional[Queue] = None,
        publish_address: Optional[PublishAddress] = None,
        retry_interval: int = 5,
        declare: bool = True,
        auto_ack: bool = True,
        prefetch_count: int = 10,
    ):
        self.queue = queue
        self.publish_address = publish_address
        self.client_id = client_id
        self.consumer_task: Optional[asyncio.Task] = None
        self.retry_interval = retry_interval
        self.declare = declare
        self.auto_ack = auto_ack
        self.prefetch_count = prefetch_count

    async def startup(self, client: RabbitMQClient, app: PubSubApp, func: Callable):
        callback = self.create_callback(client, app, func)

        loop = asyncio.get_running_loop()

        self.consumer_task = loop.create_task(
            client.consume(
                self.queue,
                callback,
                declare=self.declare,
                prefetch_count=self.prefetch_count,
            )
        )

    async def main_loop(self, client: RabbitMQClient, app: PubSubApp, func: Callable):
        while not self.should_exit:
            if self.consumer_task.done():
                task_exception = self.consumer_task.exception()
                if isinstance(task_exception, Exception):
                    logger.error(
                        f"Error in RabbitMQ: {type(task_exception).__name__}: {task_exception}. "
                        f"(Client: {self.client_id}, Queue: {self.queue.name})"
                    )

                logger.info("Attempting RabbitMQ reconnect in 5 seconds...")
                await asyncio.sleep(self.retry_interval)
                await self.startup(client, app, func)

            await asyncio.sleep(0.1)

    async def shutdown(self, client: RabbitMQClient, app: PubSubApp, func: Callable):
        logger.info("Waiting for RabbitMQ shutdown")
        await client.close()
        logger.info("Successfully shutdown RabbitMQ client")

    def create_callback(self, client: PubSubClient, app: PubSubApp, func: Callable) -> Callable:
        async def callback(msg: AbstractIncomingMessage):
            req = PubSubRequest(
                raw_data=msg.body,
                _approve=msg.ack,
                _decline=msg.nack,
                message_headers=msg.headers_raw,
                message_id=msg.message_id,
                auto_ack=self.auto_ack,
                content_encoding=msg.content_encoding,
                content_type=msg.content_type,
                extra={
                    "queue": self.queue.name,
                    "exchange": msg.exchange,
                    "routing_key": msg.routing_key
                }
            )

            res = await app(req, func)

            if self.publish_address and res is not None:
                await client.produce(
                    exchange=self.publish_address.exchange,
                    routing_key=self.publish_address.routing_key,
                    payload=res,
                )

                logger.info(f"Published message to Exchange: '{self.publish_address.exchange.name}' "
                            f"with routing key '{self.publish_address.routing_key}'")

        return callback
