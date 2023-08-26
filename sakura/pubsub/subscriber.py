from typing import Callable

from sakura.pubsub.middlewares import Middleware


class Subscriber():
    subscriber_id: str
    func: Callable
    user_middlewares: list[Middleware]

    def __init__(self, subscriber_id: str, func: Callable, middlewares: list[Middleware]):
        self.subscriber_id = subscriber_id
        self.func = func
        self.user_middlewares = middlewares if middlewares else []
