from typing import Callable, Type, TypeVar, Any

from sakura.core import Sakura
from sakura.core.logging import Logger
from sakura.core.providers import Provider
from sakura.core.settings import Settings
from sakura.core.transporters import Transporter
from sakura.core.utils.decorators import dynamic_self_func
from sakura.core.utils.factory import list_factory, dict_factory

T = TypeVar("T")


class Microservice(Sakura):
    settings: Settings
    _instance: Any = None

    def __init__(self):
        transporters = list_factory(self.settings.transporters, Transporter)
        providers = dict_factory(self.settings.providers, Provider)
        loggers = list_factory(self.settings.loggers, Logger)
        super(Microservice, self).__init__(transporters, providers, loggers)

    def __call__(self) -> Callable[[Type[T]], Type[T]]:
        def decorator(class_: Type[T]) -> Type[T]:
            orig_new = class_.__new__

            def _new_(cls, *args, **kwargs):
                if self._instance is None:
                    instance = orig_new(cls, *args, **kwargs)
                    self._instance = instance
                    class_._instance = instance

                return self._instance

            class_.__new__ = _new_

            class_.sakura_service = True
            return class_

        return decorator

    async def start(self):
        await self.setup()

        for func in self._once_functions:
            await dynamic_self_func(func, _instance=self._instance)()

        await super(Microservice, self).start()
        for provider in self._providers.values():
            await provider.teardown()

        for transporter in self._transporters:
            await transporter.teardown()



