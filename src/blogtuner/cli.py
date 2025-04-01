from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

from . import logger
from .logs import LogLevel, setup_logging
from .models import BlogConfig, BlogGenerator, CliState
from .paths import setup_target_dir


cli_state = CliState()

console = Console()


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
    cli_state.src_dir = src_dir
    setup_logging(level=log_level)


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
    blog_writer = BlogGenerator(
        blog=BlogConfig.from_directory(cli_state.src_dir), target_dir=target_dir
    )
    logger.info(f"Building site from {cli_state.src_dir} to {target_dir}")

    blog_writer.generate_site()


@app.command()
def list() -> None:
    blog = BlogConfig.from_directory(cli_state.src_dir)
    table = Table("ID", "Status", "Slug", "Title", "Date", title="Blog Posts")
    for id, post in enumerate(blog.get_sorted_posts()):
        table.add_row(
            str(id),
            "PUBLIC" if not post.draft else "DRAFT",
            post.slug,
            post.title,
            str(post.short_date),
        )

    console.print(table)


@app.command()
def version() -> None:
    import importlib.metadata

    typer.echo(importlib.metadata.version("blogtuner"))
