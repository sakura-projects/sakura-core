import inspect
import os
import re
import sys
from types import ModuleType
from typing import Any

from sakura.cli.exceptions import CommandError, UndefinedMicroserviceException, MultipleMicroservicesException
from sakura.core import Microservice


def get_classes(module: ModuleType) -> list[type]:
    classes: list[type] = []

    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj):
            classes.append(obj)

    return classes


MISSING_MODULE_TEMPLATE = "^No module named '{}'?$"
SAKURA_SERVICE = "sakura_service"


def is_microservice(obj: object):
    return isinstance(obj, Microservice)


def is_sakura_service(cls: type):
    return hasattr(cls, SAKURA_SERVICE)


def get_module(module_name: str) -> Any:
    parts = module_name.split(":", 1)
    
    if len(parts) == 1:
        module_name, obj = module_name, None
    else:
        module_name, obj = parts[0], parts[1]

    try:
        __import__(module_name)
    except ImportError as e:
        if module_name.endswith(".py") and os.path.exists(module_name):
            raise CommandError(
                "Failed to find service, did you mean '{}'?".format(
                    module_name[:3].replace('/', '.')
                )
            )

        missing_module_re = MISSING_MODULE_TEMPLATE.format(module_name)
        
        if re.match(missing_module_re, str(e)):
            raise CommandError(e)

        raise

    return sys.modules[module_name]


def initialize_service(module_name: str):
    module = get_module(module_name)
    services = [service for _, service in inspect.getmembers(module, is_sakura_service)]

    if not services:
        raise CommandError(
            "Failed to find anything that looks like a service in module "
            "{!r}".format(module_name)
        )

    if len(services) == 0:
        raise UndefinedMicroserviceException()

    if len(services) > 1:
        raise MultipleMicroservicesException()

    services[0]()


def get_microservice(module_name: str) -> Microservice:
    module = get_module(module_name)
    microservices = [microservice for _, microservice in inspect.getmembers(module, is_microservice)]

    if not microservices:
        raise CommandError(
            "Failed to find anything that looks like a microservice in module "
            "{!r}".format(module_name)
        )

    if len(microservices) == 0:
        raise UndefinedMicroserviceException()

    if len(microservices) > 1:
        raise MultipleMicroservicesException()

    return microservices[0]


