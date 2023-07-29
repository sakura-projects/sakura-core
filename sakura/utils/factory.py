from sakura.exceptions import UnsupportedClientError


# TODO: update transporters name to more generic name
def get_inheritors_dict(class_to_check: type) -> dict[str, type]:
    transporters: dict[str, type] = {class_to_check.__name__: class_to_check}
    classes_to_visit: list[type] = [class_to_check]

    while classes_to_visit:
        parent = classes_to_visit.pop()
        for child in parent.__subclasses__():
            if child not in transporters:
                transporters[child.__name__] = child
                classes_to_visit.append(child)

    return transporters


def list_factory(settings: dict, factory_type: type) -> list:
    objects = []
    inheritors_dict = get_inheritors_dict(factory_type)

    for key, value in settings.items():
        if key not in inheritors_dict:
            raise ValueError(f"Object of type {key} is not supported, check whether it's installed")

        settings = inheritors_dict[key].Settings.from_dynaconf(value)
        obj = inheritors_dict[key](settings)
        objects.append(obj)

    return objects


# TODO: remove references to provider
def dict_factory(settings: dict, parent_type: type) -> dict:
    objects: dict[str, object] = {}
    inheritors_dict = get_inheritors_dict(parent_type)

    for name, value in settings.items():
        if value["type"] not in inheritors_dict:
            raise ValueError(f"Object of type {value['type']} is not supported, check whether it's installed")

        settings = inheritors_dict[value["type"]].Settings.from_dynaconf(value["params"])

        provider = inheritors_dict[value["type"]](settings)
        objects[name] = provider

    return objects


def client_factory(settings: dict, client_type: str, factory_type: type):
    inheritors_dict = get_inheritors_dict(factory_type)

    if client_type not in inheritors_dict:
        raise UnsupportedClientError

    return inheritors_dict[client_type](**settings)
