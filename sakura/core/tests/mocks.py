from dynaconf import Dynaconf

import sakura.core
from sakura.core.providers import Provider
from sakura.core.settings import Settings, SakuraBaseSettings


class MockTransporter:
    def __init__(self):
        pass

    def __getattr__(self, item):
        # noinspection PyUnusedLocal
        def dummy_deco(*args, **kwargs):
            def dum(func):
                return func

            return dum
        return dummy_deco


class MockMicroservice(sakura.core.Microservice):
    settings: Settings
    settings_file_name = "settings.yaml"

    def __init__(self):
        new_settings = Dynaconf(
            envvar_prefix="SAKURA",
            settings_files=self.settings_file_name,
            load_dotenv=True,
        )
        self.settings = Settings.from_dynaconf(new_settings)
        super(MockMicroservice, self).__init__()

    @property
    def http(self):
        return MockTransporter()

    @property
    def pubsub(self):
        return MockTransporter()

    @property
    def cron(self):
        return MockTransporter()
