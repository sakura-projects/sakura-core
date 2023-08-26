import pkgutil

from .client import PubSubClient

__all__ = ["PubSubClient"]
for loader, module_name, _ in pkgutil.walk_packages(__path__):
    __all__.append(module_name)
    _module = loader.find_module(module_name).load_module(module_name)
    globals()[module_name] = _module
