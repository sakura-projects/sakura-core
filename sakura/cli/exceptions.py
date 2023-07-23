class CommandError(Exception):
    """Raise from subcommands to report error back to the user"""


class UndefinedMicroserviceException(Exception):
    pass


class MultipleMicroservicesException(Exception):
    pass
