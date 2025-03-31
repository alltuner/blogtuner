from importlib.resources import as_file, files
from pathlib import Path

from . import logger


def get_resource_path(directory: str) -> Path:
    with as_file(files("blogtuner.data") / directory) as resource_path:
        return resource_path


def get_static_file(name: str) -> Path:
    return get_resource_path("statics").joinpath(name)


def setup_target_dir(target_dir: Path) -> bool:
    """Ensure target directory exists, creating it if necessary."""
    if not target_dir.exists():
        target_dir.mkdir(parents=True)
        logger.info(f"Created target directory {target_dir}")
        return True

    if not target_dir.is_dir():
        logger.error(f"Target directory {target_dir} is not a directory")
        return False

    return True
