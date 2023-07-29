import logging
from typing import Callable

from fastapi import FastAPI

from sakura import Microservice

logger = logging.getLogger(__name__)


class Service(metaclass=Microservice, settings_files=["samples/basic_service/settings.yaml"], disable_uvloop=True):
    http: FastAPI
    once: Callable
    config: dict

    @once
    async def run(self):
        logger.info("Started service")

    @http.get("/")
    async def root(self, args):
        return {"foo": "bar"}
