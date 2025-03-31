import logging
from enum import StrEnum
from pathlib import Path

import typer
from typing_extensions import Annotated

from . import logger
from .models import Blog, BlogWriter, CliState
from .paths import setup_target_dir


cli_state = CliState()


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


app = typer.Typer(no_args_is_help=True)


@app.callback(invoke_without_command=True)
def main(
    log_level: Annotated[
        LogLevel,
        typer.Option(
            envvar="BLOGTUNER_LOG_LEVEL",
            help="Set the logging level",
            show_default=False,
        ),
    ] = LogLevel.INFO,
    src_dir: Annotated[
        Path,
        typer.Option(
            envvar="BLOGTUNER_SRC_DIR",
            help="The source directory to build from",
            exists=True,
            dir_okay=True,
            file_okay=False,
            resolve_path=True,
        ),
    ] = Path("."),
) -> None:
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    cli_state.src_dir = src_dir


@app.command()
def build(
    target_dir: Annotated[
        Path,
        typer.Argument(
            envvar="BLOGTUNER_TARGET_DIR",
            help="The target directory to build to",
        ),
    ],
) -> None:
    setup_target_dir(target_dir)
    blog_writer = BlogWriter(
        blog=Blog.from_src_dir(cli_state.src_dir), target_dir=target_dir
    )
    logger.info(f"Building site from {cli_state.src_dir} to {target_dir}")

    blog_writer.generate()


@app.command()
def list() -> None:
    typer.echo("List list posts")
    logger.info("List posts")
    logger.debug("Debugging list posts")


@app.command()
def version() -> None:
    import importlib.metadata

    typer.echo(importlib.metadata.version("blogtuner"))
