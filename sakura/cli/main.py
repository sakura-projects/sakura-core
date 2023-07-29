import logging
import os
import sys
from typing import Optional

import typer
from dynaconf import Dynaconf

from sakura.cli.asyncio_utils import initialize_loop
from sakura.cli.utils import initialize_service

sys.path.append(os.getcwd())

app = typer.Typer()


@app.command()
def run(
    module_name: str,
    settings_path: Optional[list[str]] = typer.Option(['settings.yaml'], '--settings', '-s'),
    load_dotenv: Optional[bool] = typer.Option(False, '--load-dotenv'),
    disable_uvloop: Optional[bool] = typer.Option(False, '--disable-uvloop'),
    debug: Optional[bool] = typer.Option(False, '--debug'),
):
    initialize_service(module_name)
    # use_uvloop = not disable_uvloop
    #
    # if debug:
    #     logging.getLogger('sakura').setLevel(logging.DEBUG)
    #
    # if use_uvloop:
    #     try:
    #         import uvloop
    #     except ImportError:
    #         logging.getLogger('sakura').error('Please install uvloop or consider running with the --disable-uvloop flag')
    #         return
    #
    # initialize_loop(use_uvloop=use_uvloop)
    #
    # settings = Dynaconf(
    #     envvar_prefix="SAKURA",
    #     settings_files=settings_path,
    #     load_dotenv=load_dotenv,
    # )


@app.command(name='info')
def get_info(module_name: str):
    typer.echo(module_name)


def main():
    app()


if __name__ == "__main__":
    main()

