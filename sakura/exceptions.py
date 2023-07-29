import pydantic


class HTTPTransporterNotInitialized(Exception):
    pass


class PubSubTransporterNotInitialized(Exception):
    pass


class MissingParameterException(Exception):
    pass


class InvalidParameterTypeException(Exception):
    pass


class ValidationException(Exception):
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


class UnsupportedClientException(Exception):
    pass


class ClientNotFoundException(Exception):
    pass


class DecodeError(Exception):
    pass


class PropertyDoesntExist(Exception):
    pass
