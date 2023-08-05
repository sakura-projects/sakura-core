import asyncio
import logging
from typing import Callable, Optional

from sakura.pubsub.rabbitmq.rabbitmq_client import RabbitMQClient
from sakura.pubsub.rabbitmq.settings import SubscriberSettings
from sakura.pubsub.subscriber import Subscriber

logger = logging.getLogger(__name__)


class RabbitMQSubscriber(Subscriber):
    should_exit: bool = False

    def __init__(self, settings: SubscriberSettings, client: RabbitMQClient, func: Callable, subscriber_id: str):
        self.client = client
        self.func = func
        self.subscriber_id = subscriber_id
        self.queue = settings.queue
        self.auto_ack = settings.auto_ack
        self.prefetch_count = settings.prefetch_count
        self.retry_interval = settings.retry_interval

        self.consumer_task: Optional[asyncio.Task] = None

    async def run(self):
        await self.startup()
        await self.main_loop()
        await self.shutdown()

    async def consume(self, queue: str, callback: Callable):
        async with self.client.get_channel() as channel:
            await channel.set_qos(prefetch_count=self.prefetch_count)
            rmq_queue = await channel.get_queue(queue, ensure=True)

            logger.info(f'Consuming queue: "{queue}"')
            await rmq_queue.consume(callback)
            await asyncio.Future()

    async def startup(self):
        loop = asyncio.get_running_loop()

        self.consumer_task = loop.create_task(
            self.consume(self.queue, self.func),
        )

    async def main_loop(self):
        while not self.should_exit:
            if self.consumer_task.done():
                task_exception = self.consumer_task.exception()
                if isinstance(task_exception, Exception):
                    logger.error(
                        f"Error in RabbitMQ: {type(task_exception).__name__}: {task_exception}. "
                        f"(Client: {self.subscriber_id}, Queue: {self.queue})",
                    )

                logger.info("Attempting RabbitMQ reconnect in 5 seconds...")
                await asyncio.sleep(self.retry_interval)
                await self.startup()

            await asyncio.sleep(0.1)

    async def shutdown(self):
        logger.info("Waiting for RabbitMQ shutdown")
        await self.client.close()
        logger.info("Successfully shutdown RabbitMQ client")
