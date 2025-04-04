from pathlib import Path

import typer
from typing_extensions import Annotated

from blogtuner.cli.core import cli_state
from blogtuner.cli.post import post_app
from blogtuner.core.blog import BlogConfig
from blogtuner.rendering.site import build_site
from blogtuner.utils.logs import LogLevel, setup_logging


app = typer.Typer(no_args_is_help=True)
app.add_typer(post_app, name="post", help="Manage blog posts")


@app.callback(invoke_without_command=False)
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
    cli_state.src_dir = src_dir
    setup_logging(level=log_level)


@app.command(help="Build the blog site")
def build(
    target_dir: Annotated[
        Path,
        typer.Argument(
            envvar="BLOGTUNER_TARGET_DIR", help="The target directory to build to"
        ),
    ],
) -> None:
    build_site(target_dir, BlogConfig.from_directory(cli_state.src_dir))


@app.command(help="Show the version of the application")
def version() -> None:
    import importlib.metadata

    typer.echo(importlib.metadata.version("blogtuner"))
