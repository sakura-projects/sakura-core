import functools
import signal
from types import FrameType

from sakura.core.settings import SakuraBaseSettings, Client
from sakura.core.transporters import Transporter
from sakura.core.transporters.http.http_client import HTTPClient
from sakura.core.utils.decorators import dynamic_self_func
from sakura.core.utils.factory import client_factory


class HTTPTransporter(Transporter):
    class Settings(SakuraBaseSettings):
        client: Client

    http_client: HTTPClient

    def __init__(self, settings: Settings):
        self.__settings = settings
        self.http_client = client_factory(
            self.__settings.client.params,
            self.__settings.client.type,
            HTTPClient,
        )

    async def generate_tasks(self):
        return [self.http_client.serve()]

    @property
    def http(self):
        original_self = self

        class C:
            def __getattr__(self, name: str):
                method = getattr(original_self.http_client, name)

                def wildcard_method(*args, **kwargs):
                    result = method(*args, **kwargs)
                    return lambda f: result(dynamic_self_func(f))

                return functools.wraps(method)(wildcard_method)

        return C()

    def handle_exit(self, sig: signal.Signals, frame: FrameType) -> None:
        self.http_client.handle_exit(sig, frame)
