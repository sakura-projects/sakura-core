import asyncio
import signal
from types import FrameType
from typing import Callable

from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.base import BaseTrigger
from pytz_deprecation_shim import PytzUsageWarning

from sakura.core.transporters import Transporter
from sakura.core.settings import SakuraBaseSettings
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from sakura.core.utils.decorators import dynamic_self_func
from sakura.core.utils.types import DecoratedCallable

from warnings import filterwarnings
filterwarnings(action="ignore", category=PytzUsageWarning, module="apscheduler")


class CronTransporter(Transporter):
    class Settings(SakuraBaseSettings):
        pass

    __job_store: list[tuple[Callable, BaseTrigger]]
    __scheduler: AsyncIOScheduler

    loop_future: asyncio.Future

    def __init__(self):
        self.__job_store = []

    async def setup(self):
        self.__scheduler = AsyncIOScheduler({"event_loop": asyncio.get_running_loop()})

        for func, trigger in self.__job_store:
            self.__scheduler.add_job(func, trigger)

    def __call__(self, weeks=0, days=0, hours=0, minutes=0, seconds=0, start_date=None,
                 end_date=None, timezone=None, jitter=None) -> DecoratedCallable:
        def decorator(func: Callable):
            new_func = dynamic_self_func(func)
            trigger = IntervalTrigger(
                weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds, start_date=start_date,
                end_date=end_date, timezone=timezone, jitter=jitter,
            )

            self.__job_store.append((new_func, trigger))

        return decorator
    
    async def loop(self):
        await self.loop_future
    
    async def generate_tasks(self) -> list:
        self.__scheduler.start()
        self.loop_future = asyncio.Future()
        return [self.loop()]

    def handle_exit(self, sig: signal.Signals, frame: FrameType) -> None:
        self.loop_future.set_result(True)
        self.__scheduler.remove_all_jobs()
