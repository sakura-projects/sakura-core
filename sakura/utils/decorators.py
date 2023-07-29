import functools
import inspect
from typing import Callable, Any


def get_class_that_defined_method(method):
    if inspect.ismethod(method):
        for cls in inspect.getmro(method.__self__.__class__):
            if cls.__dict__.get(method.__name__) is method:
                return cls

        method = method.__func__

    if inspect.isfunction(method):
        class_name = method.__qualname__.split(".<locals>", 1)[0].rsplit(".", 1)[0]

        try:
            cls = getattr(inspect.getmodule(method), class_name)
        except AttributeError:
            cls = method.__globals__.get(class_name)
        
        if isinstance(cls, type):
            return cls


class DynamicSelfFunc:
    _instance: Any

    def __init__(self, func: Callable):
        self.func = func

    def __call__(self, *args, **kwargs):
        old_signature = inspect.signature(self.func)

        @functools.wraps(self.func)
        def sync_decorator(*deco_args, **deco_kwargs):
            if len(old_signature.parameters) == len(deco_args + tuple(deco_kwargs.values())):
                return self.func(*deco_args, **deco_kwargs)
            else:
                return self.func(self._instance, *deco_args, **deco_kwargs)

        @functools.wraps(self.func)
        async def async_decorator(*deco_args, **deco_kwargs):
            if len(old_signature.parameters) == len(deco_args + tuple(deco_kwargs.values())):
                return await self.func(*deco_args, **deco_kwargs)
            else:
                return await self.func(self._instance, *deco_args, **deco_kwargs)

        decorator = async_decorator if inspect.iscoroutinefunction(self.func) else sync_decorator

        params = [param for param in old_signature.parameters.values() if param.name != 'self']
        decorator.__signature__ = old_signature.replace(parameters=params)
        return decorator
