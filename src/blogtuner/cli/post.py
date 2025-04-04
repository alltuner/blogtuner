import typer
from rich.table import Table
from typing_extensions import Annotated

from blogtuner.cli.core import cli_state, console
from blogtuner.cli.importer import import_app
from blogtuner.core.blog import BlogConfig


post_app = typer.Typer(no_args_is_help=True)
post_app.add_typer(import_app, name="import", help="Import blog posts")


@post_app.callback(invoke_without_command=True)
def post_callback() -> None:
    console.print("If you make any changes, please remember to rebuild the site.")


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
