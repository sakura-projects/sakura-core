from sakura.core.microservice import Microservice


microservice = Microservice()


@microservice()
class Service:
    @microservice.once
    async def run(self):
        print("Hello World")
