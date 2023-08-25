import asyncio
from contextlib import asynccontextmanager
from logging import getLogger
from typing import Optional

import aio_pika
from aio_pika.abc import (
    AbstractExchange,
    AbstractIncomingMessage,
    AbstractQueue,
    AbstractRobustChannel,
    AbstractRobustConnection,
    DeliveryMode,
)
from aio_pika.pool import Pool

from sakura.pubsub.rabbitmq.rabbitmq_client.types import Exchange, Queue

logger = getLogger(__name__)

class RabbitMQClient:
    __queues: dict[str, AbstractQueue]
    _connection_pool: Pool[AbstractRobustConnection]
    _channel_pool: Pool[AbstractRobustChannel]
    __queues_lock: asyncio.Lock = asyncio.Lock()
    is_open: bool = False

    def __init__(self, uri: str, virtual_host: str, encoding: str, content_type: str):
        self.uri = uri
        self.virtual_host = virtual_host
        self.encoding = encoding
        self.content_type = content_type
        self.__queues = {}

    async def setup(self):
        self.is_open = True
        self._connection_pool = Pool(self.get_connection)
        self._channel_pool = Pool(self._get_channel)

    async def close(self):
        if self.is_open:
            self.is_open = False
            await self._channel_pool.close()
            await self._connection_pool.close()

    async def get_connection(self) -> AbstractRobustConnection:
        return await aio_pika.connect_robust(self.uri, virtualhost=self.virtual_host)

    async def _get_channel(self):
        async with self._connection_pool.acquire() as connection:
            return await connection.channel()

    @asynccontextmanager
    async def get_channel(self) -> AbstractRobustChannel:
        async with self._channel_pool.acquire() as channel:
            yield channel

    @staticmethod
    async def _get_exchange(exchange: Exchange, channel: AbstractRobustChannel, declare: bool = True):
        if declare:
            return await channel.declare_exchange(
                name=exchange.name,
                type=exchange.type,
                durable=exchange.durable,
                arguments=exchange.arguments,
                auto_delete=False,
            )

        return await channel.get_exchange(exchange.name, ensure=False)

    async def _get_queue(self, queue: Queue, channel: AbstractRobustChannel, declare: bool = False):
        async with self.__queues_lock:
            if rmq_queue := self.__queues.get(queue.name):
                return rmq_queue

        if declare:
            rmq_queue = await channel.declare_queue(
                name=queue.name,
                durable=queue.durable,
                exclusive=queue.exclusive,
                arguments=queue.arguments,
                auto_delete=False,
            )

            if queue.exchange:
                exchange: AbstractExchange = await RabbitMQClient._get_exchange(
                    exchange=queue.exchange,
                    channel=channel,
                )

                routing_key = queue.routing_key or queue.name
                await rmq_queue.bind(exchange, routing_key)

        rmq_queue = await channel.get_queue(queue.name, ensure=True)

        async with self.__queues_lock:
            if rmq_queue.name not in self.__queues:
                self.__queues[rmq_queue.name] = rmq_queue

        return rmq_queue

    async def get_exchange(self, exchange: Exchange):
        async with self.get_channel() as channel:
            return await self._get_exchange(exchange, channel)

    async def get_queue(self, queue: Queue, declare: bool = False):
        async with self.__queues_lock:
            if rmq_queue := self.__queues.get(queue.name):
                return rmq_queue

        async with self.get_channel() as channel:
            self.__queues[queue.name] = await self._get_queue(queue, channel, declare)
            async with self.__queues_lock:
                return self.__queues[queue.name]

    async def __get_message(self, queue: AbstractQueue, timeout: int = 1) -> Optional[AbstractIncomingMessage]:
        message: AbstractIncomingMessage = await queue.get(timeout=5, fail=False)
        if message is None:
            await asyncio.sleep(timeout)
            return await queue.get(timeout=5, fail=False)
        return None

    async def get_message(self, queue: Queue, timeout: int = 1) -> Optional[AbstractIncomingMessage]:
        async with self.get_channel() as channel:
            queue = await self._get_queue(queue, channel)
            message: AbstractIncomingMessage = await self.__get_message(queue, timeout)
            return message

    async def get_messages(self, queue: Queue, count: int, timeout: int = 1) -> list[AbstractIncomingMessage]:
        messages: list[AbstractIncomingMessage] = []
        async with self.get_channel() as channel:
            await channel.set_qos(prefetch_count=count)
            queue = await self._get_queue(queue, channel)
            for _ in range(count):
                message: AbstractIncomingMessage = await self.__get_message(queue, timeout)
                if message:
                    messages.append(message)
                else:
                    break
            return messages

    async def stream_get_messages(self, queue: Queue, count: int, max_time_between_messages: int = 1):
        async with self.get_channel() as channel:
            await channel.set_qos(prefetch_count=count)
            queue = await self._get_queue(queue, channel)
            message_c = 0
            async with queue.iterator(timeout=max_time_between_messages) as q:
                try:
                    async for message in q:
                        yield message
                        message_c += 1
                        if message_c == count:
                            return
                except asyncio.exceptions.TimeoutError:
                    return

    async def ack_messages(self, messages: list[AbstractIncomingMessage]):
        for message in messages:
            await message.ack()

    async def produce(  # noqa: PLR0913
        self,
        exchange: Exchange,
        routing_key: str,
        payload: dict,
        delivery_mode: DeliveryMode = DeliveryMode.PERSISTENT,
        declare: bool = True,
    ):
        message = await self.create_message_from_payload(payload, delivery_mode=delivery_mode)
        async with self.get_channel() as channel:
            exchange = await self._get_exchange(exchange, channel, declare)
            await exchange.publish(message, routing_key)
