from pathlib import Path

import typer
from typing_extensions import Annotated


app = typer.Typer(no_args_is_help=True)


@app.command()
def build(
    source_dir: Annotated[
        Path, typer.Argument(help="The source directory to build from")
    ],
    target_dir: Annotated[
        Path, typer.Argument(help="The target directory to build to")
    ],
) -> None:
    if not source_dir.exists():
        raise typer.BadParameter(f"Source directory '{source_dir}' does not exist")

    from .build import build_site

    build_site(source_dir, target_dir)


@app.command()
def version() -> None:
    import importlib.metadata

    typer.echo(importlib.metadata.version("blogtuner"))
