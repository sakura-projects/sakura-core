from sakura.core.microservice import Microservice
from sakura.core.transporters.http.fastapi import FastAPI


microservice = Microservice()


@microservice()
class Service:
    http: FastAPI = microservice.http
    once = microservice.once

    @once
    async def run(self):
        print("Hello World")

    @http.get('/')
    async def root(self):
        return {'foo': 'bar'}
