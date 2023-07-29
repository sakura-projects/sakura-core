import asyncio
import logging
import inspect

from pydantic.fields import ErrorWrapper

from asyncer import asyncify
from fastapi.dependencies.utils import get_typed_signature, get_param_field

from sakura.core.pubsub.types import PubSubRequest, PubSubApp
from sakura.core.utils.decorators import DynamicSelfFunc
from sakura.core.utils.types import DecoratedCallable

logger = logging.getLogger(__name__)


class ExecuteMiddleware(PubSubApp):
    async def __call__(self, request: PubSubRequest, handler: DecoratedCallable):
        new_handler = DynamicSelfFunc(handler)()
        endpoint_signature = get_typed_signature(new_handler)

        values, errors = self.request_payload_to_args(endpoint_signature, request)

        if len(errors) > 0:
            raise ValueError(f"Error in {request.message_id=}: {errors}")

        if not asyncio.iscoroutinefunction(new_handler):
            new_handler = asyncify(new_handler)

        return await new_handler(**values)

    @staticmethod
    def request_payload_to_args(endpoint_signature: inspect.Signature, request: PubSubRequest) -> tuple[dict, list]:
        signature_params = endpoint_signature.parameters
        values, errors = {}, []
        received_payload = request.data
        body_params = []
        request_param_name = None
        for param_name, param in signature_params.items():
            if isinstance(param.annotation, type) and issubclass(param.annotation, PubSubRequest):
                request_param_name = param_name
                continue
            body_params.append(get_param_field(param=param, param_name=param_name))
        
        if body_params:
            field = body_params[0]
            field_info = field.field_info
            embed = getattr(field_info, "embed", None)
            field_alias_omitted = len(body_params) == 1 and not embed
            
            if field_alias_omitted:
                received_payload = {field.alias: received_payload}
            
            for field in body_params:
                param_name = field.alias
                value = received_payload.get(param_name)
                loc: tuple[str, ...]
                if field_alias_omitted:
                    loc = ("payload",)
                else:
                    loc = ("payload", param_name)

                values_, errors_ = field.validate(value, received_payload, loc=loc)

                if isinstance(errors_, ErrorWrapper):
                    errors.append(errors_)
                elif isinstance(errors_, list):
                    errors.extend(errors_)
                else:
                    values[field.name] = values_

            if request_param_name:
                values[request_param_name] = request

            return values, errors
