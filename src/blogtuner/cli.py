from pathlib import Path

import typer
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

from .builder import build_site
from .importer import import_substack_posts
from .logs import LogLevel, setup_logging
from .models import BlogConfig


class CliState(BaseModel):
    src_dir: Path = Path(".")


cli_state = CliState()
console = Console()


app = typer.Typer(no_args_is_help=True)
import_app = typer.Typer(no_args_is_help=True)
post_app = typer.Typer(no_args_is_help=True)
app.add_typer(post_app, name="post", help="Manage blog posts")
post_app.add_typer(import_app, name="import", help="Import blog posts")


@post_app.callback(invoke_without_command=True)
def post_callback() -> None:
    console.print("If you make any changes, please remember to rebuild the site.")


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


@post_app.command(help="List all blog posts")
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


@post_app.command(help="Unpublish a blog post", name="unpublish")
def post_unpublish(
    slug: Annotated[
        str,
        typer.Argument(
            help="The slug of the post to unpublish",
        ),
    ],
) -> None:
    blog = BlogConfig.from_directory(cli_state.src_dir)
    blog.unpublish_post(slug)


@post_app.command(help="Publish a blog post", name="publish")
def post_publish(
    slug: Annotated[
        str,
        typer.Argument(
            help="The slug of the post to publish",
        ),
    ],
) -> None:
    blog = BlogConfig.from_directory(cli_state.src_dir)
    blog.publish_post(slug)


@post_app.command(help="Delete a blog post", name="delete")
def post_delete(
    slug: Annotated[
        str,
        typer.Argument(
            help="The slug of the post to delete",
        ),
    ],
) -> None:
    blog = BlogConfig.from_directory(cli_state.src_dir)
    blog.delete_post(slug)


@import_app.command(help="Import a markdown file as a blog post", name="markdown")
def import_markdown(
    markdown_file: Annotated[
        Path,
        typer.Argument(
            help="The markdown file to import as a blog post",
            exists=True,
            dir_okay=False,
            file_okay=True,
            resolve_path=True,
            readable=True,
        ),
    ],
) -> None:
    blog = BlogConfig.from_directory(cli_state.src_dir)
    blog.import_markdown_file(markdown_file)


@import_app.command(help="Import all the posts of a substack blog", name="substack")
def import_substack(
    substack_url: Annotated[
        str,
        typer.Argument(
            help="The substack URL to import posts from",
        ),
    ],
) -> None:
    blog = BlogConfig.from_directory(cli_state.src_dir)

    import_substack_posts(substack_url, blog.used_slugs, cli_state.src_dir)


@app.command(help="Show the version of the application")
def version() -> None:
    import importlib.metadata

    typer.echo(importlib.metadata.version("blogtuner"))
