import functools
import inspect
import logging
import typing

from sakura.pubsub.middlewares import Middleware

if typing.TYPE_CHECKING:
    from aio_pika.abc import AbstractIncomingMessage

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    pass


class ExecutionMiddleware(Middleware):
    def __init__(self, auto_ack: bool = False):
        self.auto_ack = auto_ack

    @staticmethod
    def validate_request(func: typing.Callable, received_params: dict) -> dict[str, typing.Any]:
        values: dict[str, typing.Any] = {}
        errors: list[str] = []

        for param in inspect.signature(func).parameters.values():
            if param.name not in received_params and param.default is inspect.Parameter.empty:
                errors.append(f"Param <{param}> is missing")
            elif param.name in received_params and not isinstance(received_params[param.name], param.annotation):
                errors.append(f"Param <{param}> is of the wrong type, "
                                f"expected {param.annotation} got {type(received_params[param.name])}")
            elif param.name not in received_params and param.default is not inspect.Parameter.empty:
                values[param.name] = param.default
            else:
                values[param.name] = received_params[param.name]

        if errors:
            raise ValidationError("\n".join(errors))
        
        return values

    
    def __call__(self, func: typing.Callable) -> typing.Callable:
        @functools.wraps(func)
        async def wrapper(*_, **kwargs):
            values = self.validate_request(func=func, received_params=kwargs)

            await func(**values)

            msg: AbstractIncomingMessage = kwargs.get("_msg")

            if self.auto_ack:
                await msg.ack()
                logger.debug(f"Acknowledged {msg.message_id}")

        return wrapper