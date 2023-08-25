import pydantic


class HTTPTransporterNotInitializedError(Exception):
    pass


class PubSubTransporterNotInitializedError(Exception):
    pass


class MissingParameterError(Exception):
    pass


class InvalidParameterTypeError(Exception):
    pass


class ValidationError(Exception):
    @classmethod
    def from_pydantic(cls, pydantic_error: pydantic.ValidationError):
        errors = [
            {
                "field": ".".join(error["loc"]),
                "error": error["msg"],
            }
            for error in pydantic_error.errors()
        ]

        return cls(str(errors))


class UnsupportedClientError(Exception):
    pass


class ClientNotFoundError(Exception):
    pass


class SubscriberNotFoundError(Exception):
    pass


class DecodeError(Exception):
    pass


class PropertyDoesntExistError(Exception):
    pass
