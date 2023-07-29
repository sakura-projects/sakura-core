from typing import TypeVar, Callable, Any

DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., Any])
