def merge_dicts(a: dict, b: dict, path=None):
    path = [] if path is None else path
    for key in b:
        if key in a:
            if isinstance(a[key], list) and isinstance(b[key], list):
                a[key] += b[key]
            elif isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_dicts(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass
            else:
                raise ValueError(f"Conflict at {'.'.join(path + [str(key)])}")
        else:
            a[key] = b[key]

    return a
