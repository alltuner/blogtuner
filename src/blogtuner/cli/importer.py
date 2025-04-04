from pathlib import Path

import typer
from typing_extensions import Annotated

from blogtuner.cli.core import cli_state
from blogtuner.core.blog import BlogConfig
from blogtuner.importers.substack import import_substack_posts


import_app = typer.Typer(
    no_args_is_help=True,
)


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
