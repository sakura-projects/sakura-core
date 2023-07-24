import logging

from sakura.core.microservice import Microservice
from sakura.core.transporters.http.fastapi import FastAPI

from sakura.core.rabbitmq.types import Exchange, Queue
from sakura.core.rabbitmq.rabbitmq_subscriber import RabbitMQSubscriber
from sakura.core.transporters.pubsub import PubSubTransporter

microservice = Microservice()


@microservice()
class Service:
    http: FastAPI = microservice.http
    pubsub: PubSubTransporter = microservice.pubusub
    once = microservice.once
    config = microservice.settings.config

    exchange = Exchange(name=config['exchange']['name'])
    queue = Queue(name=config['queue']['name'], exchange=exchange, routing_key='route_a')

    subscriber = RabbitMQSubscriber(client_id='first_client', queue=queue, declare=True)

    logger = logging.getLogger(__name__)

    @once
    async def run(self):
        self.logger.info('Started service')

    @http.get('/')
    async def root(self):
        return {'foo': 'bar'}

    @pubsub.subscribe(subscriber=subscriber)
    async def read_from_queue(self, id: int, name: str):
        self.logger.info(f'{id} hello: {name}')
