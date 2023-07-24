import functools
import inspect


def get_class_that_defined_method(method):
    if inspect.ismethod(method):
        for cls in inspect.getmro(method.__self__.__class__):
            if cls.__dict__.get(method.__name__) is method:
                return cls

        method = method.__func__ # fallback to __qualname__ parsing

    if inspect.isfunction(method):
        class_name = method.__qualname__.split(".<locals>", 1)[0].rsplit(".", 1)[0]

        try:
            cls = getattr(inspect.getmodule(method), class_name)
        except AttributeError:
            cls = method.__globals__.get(class_name)
        
        if isinstance(cls, type):
            return cls


def dynamic_self_func(func, _instance=None):
    old_signature = inspect.signature(func)

    @functools.wraps(func)
    def sync_decorator(*args, **kwargs):
        nonlocal _instance

        if not _instance:
            cls = get_class_that_defined_method(func)
            # noinspection PyUnresolvedReferences
            _instance = cls._instance

        if len(old_signature.parameters) == len(args + tuple(kwargs.values())):
            return func(*args, **kwargs)
        else:
            return func(_instance, *args, **kwargs)

    @functools.wraps(func)
    async def async_decorator(*args, **kwargs):
        nonlocal _instance

        if not _instance:
            cls = get_class_that_defined_method(func)
            # noinspection PyUnresolvedReferences
            _instance = cls._instance

        if len(old_signature.parameters) == len(args + tuple(kwargs.values())):
            return await func(*args, **kwargs)
        else:
            return await func(_instance, *args, **kwargs)

    decorator = async_decorator if inspect.iscoroutinefunction(func) else sync_decorator

    params = [param for param in old_signature.parameters.values() if param.name != 'self']
    decorator.__signature__ = old_signature.replace(parameters=params)
    return decorator
