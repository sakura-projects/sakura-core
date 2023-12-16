import pkgutil

__all__ = ("Provider",)
for loader, module_name, _ in pkgutil.walk_packages(__path__):
    __all__ += (module_name,)  # noqa: PLE0604
    _module = loader.find_module(module_name).load_module(module_name)
    globals()[module_name] = _module
