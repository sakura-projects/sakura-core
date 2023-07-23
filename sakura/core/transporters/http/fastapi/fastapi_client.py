import asyncio
import logging
import os
import signal
from types import FrameType
from typing import (
    Any,
    Callable,
    Coroutine,
    Optional,
    Sequence,
    Type,
    Union,
)

import fastapi
from fastapi import routing
from fastapi.datastructures import Default
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.params import Depends
from fastapi.staticfiles import StaticFiles
from fastapi.utils import generate_unique_id
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute
from uvicorn import Server, Config
import uvicorn.server

from sakura.core.logging.loguru import InterceptHandler
from sakura.core.transporters.http.http_client import HTTPClient


class FastAPI(fastapi.FastAPI, HTTPClient):
    server: Server

    def __init__(
        self,
        *,
        port: int = "8080",
        debug: bool = False,
        routes: Optional[list[BaseRoute]] = None,
        title: str = "FastAPI",
        description: str = "",
        version: str = "0.1.0",
        openapi_url: Optional[str] = "/openapi.json",
        openapi_tags: Optional[list[dict[str, Any]]] = None,
        servers: Optional[list[dict[str, Union[str, Any]]]] = None,
        dependencies: Optional[Sequence[Depends]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        swagger_ui_oauth2_redirect_url: Optional[str] = "/docs/oauth2-redirect",
        swagger_ui_init_oauth: Optional[dict[str, Any]] = None,
        middleware: Optional[Sequence[Middleware]] = None,
        exception_handlers: Optional[
            dict[
                Union[int, Type[Exception]],
                Callable[[Request, Any], Coroutine[Any, Any, Response]],
            ]
        ] = None,
        on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
        terms_of_service: Optional[str] = None,
        contact: Optional[dict[str, Union[str, Any]]] = None,
        license_info: Optional[dict[str, Union[str, Any]]] = None,
        openapi_prefix: str = "",
        root_path: str = "",
        root_path_in_servers: bool = True,
        responses: Optional[dict[Union[int, str], dict[str, Any]]] = None,
        callbacks: Optional[list[BaseRoute]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        swagger_ui_parameters: Optional[dict[str, Any]] = None,
        generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(
            generate_unique_id
        ),
        **extra: Any,
    ):
        super().__init__(
            docs_url=None,
            redoc_url=None,
            debug=debug,
            routes=routes,
            title=title,
            description=description,
            version=version,
            openapi_url=openapi_url,
            openapi_tags=openapi_tags,
            servers=servers,
            dependencies=dependencies,
            default_response_class=default_response_class,
            swagger_ui_oauth2_redirect_url=swagger_ui_oauth2_redirect_url,
            swagger_ui_init_oauth=swagger_ui_init_oauth,
            middleware=middleware,
            exception_handlers=exception_handlers,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            terms_of_service=terms_of_service,
            contact=contact,
            license_info=license_info,
            openapi_prefix=openapi_prefix,
            root_path=root_path,
            root_path_in_servers=root_path_in_servers,
            responses=responses,
            callbacks=callbacks,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            swagger_ui_parameters=swagger_ui_parameters,
            generate_unique_id_function=generate_unique_id_function,
            **extra,
        )

        self.port = port

        static_files_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
        self.mount("/static", StaticFiles(directory=static_files_path))

        @self.get("/docs", include_in_schema=False)
        async def custom_swagger_ui_html():
            return get_swagger_ui_html(
                openapi_url=self.openapi_url,
                title=self.title + " - Swagger UI",
                oauth2_redirect_url=self.swagger_ui_oauth2_redirect_url,
                swagger_js_url="/static/swagger-ui-bundle.js",
                swagger_css_url="/static/swagger-ui.css",
            )

        @self.get(self.swagger_ui_oauth2_redirect_url, include_in_schema=False)
        async def swagger_ui_redirect():
            return get_swagger_ui_oauth2_redirect_html()


        @self.get("/redoc", include_in_schema=False)
        async def redoc_html():
            return get_redoc_html(
                openapi_url=self.openapi_url,
                title=self.title + " - ReDoc",
                redoc_js_url="/static/redoc.standalone.js",
            )

    # noinspection PyTypeChecker
    async def serve(self):
        loop = asyncio.get_running_loop()

        config = Config(
            self,
            host='0.0.0.0',
            port=self.port,
            loop=loop,
        )

        self.server = Server(config=config)
        logging.getLogger("uvicorn").removeHandler(logging.getLogger("uvicorn").handlers[0])
        logging.getLogger("uvicorn.access").removeHandler(logging.getLogger("uvicorn.access").handlers[0])

        logging.getLogger("uvicorn.access").addHandler(InterceptHandler())

        # Remove uvicorn signal handling
        uvicorn.server.HANDLED_SIGNALS = tuple()

        await self.server.serve()

    def handle_exit(self, sig: signal.Signals, frame: FrameType) -> None:
        self.server.handle_exit(sig, frame)
