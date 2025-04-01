from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

from .builder import build_site
from .logs import LogLevel, setup_logging
from .models import BlogConfig, CliState


cli_state = CliState()

console = Console()


app = typer.Typer(no_args_is_help=True)
import_app = typer.Typer(no_args_is_help=True)
app.add_typer(import_app, name="import", help="Import blog posts")


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


@app.command(help="List all blog posts")
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


@import_app.command(help="Import a markdown file as a blog post")
def markdown(
    markdown_file: Annotated[
        Path,
        typer.Argument(
            help="The source directory to build from",
            exists=True,
            dir_okay=False,
            file_okay=True,
            resolve_path=True,
            readable=True,
        ),
    ],
    target_dir: Annotated[
        Path,
        typer.Argument(
            envvar="BLOGTUNER_TARGET_DIR", help="The target directory to build to"
        ),
    ],
) -> None:
    blog = BlogConfig.from_directory(cli_state.src_dir)
    blog.import_markdown_file(markdown_file)

    build_site(target_dir, blog)


@app.command(help="Show the version of the application")
def version() -> None:
    import importlib.metadata

    typer.echo(importlib.metadata.version("blogtuner"))
