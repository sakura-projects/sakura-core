from sakura.utils.factory import get_inheritors_dict


def pubsub_factory(settings: dict, parent_type: type) -> dict:
    objects: dict[str, object] = {}
    inheritors_dict = get_inheritors_dict(parent_type)

    for name, value in settings.items():
        if value["type"] not in inheritors_dict:
            # TODO: raise the ValueError
            # raise ValueError(f"Object of type {value['type']} is not supported, check whether it's installed")
            continue

        settings = inheritors_dict[value["type"]].Settings.from_dynaconf(value)

        object_ = inheritors_dict[value["type"]](settings)
        objects[name] = object_

    return objects
