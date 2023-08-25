from dynaconf import Dynaconf

import sakura
from sakura.settings import Settings


class MockTransporter:
    def __init__(self):
        pass

    def __getattr__(self, item):
        def dummy_deco(*args, **kwargs):   # noqa: ARG001
            def dum(func):
                return func

            return dum
        return dummy_deco


class MockMicroservice(sakura.Microservice):
    settings: Settings
    settings_file_name = "settings.yaml"

    def __init__(self):
        new_settings = Dynaconf(
            envvar_prefix="SAKURA",
            settings_files=self.settings_file_name,
            load_dotenv=True,
        )
        self.settings = Settings.from_dynaconf(new_settings)
        super().__init__()

    @property
    def http(self):
        return MockTransporter()

    @property
    def pubsub(self):
        return MockTransporter()
