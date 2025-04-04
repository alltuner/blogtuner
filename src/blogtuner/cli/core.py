from pathlib import Path

from pydantic import BaseModel
from rich.console import Console


class CliState(BaseModel):
    src_dir: Path = Path(".")


cli_state = CliState()

console = Console()
