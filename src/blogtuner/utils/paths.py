import mimetypes
from importlib.resources import as_file, files
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

from blogtuner.utils.logs import logger


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


def save_image(url: str, save_dir: Path, stem: str) -> Path:
    # Create the directory if it doesn't exist
    if not save_dir.exists():
        raise FileNotFoundError(f"Directory {save_dir} does not exist.")

    # Get the image data
    response = requests.get(url, stream=True, timeout=10)
    response.raise_for_status()

    # Try to get the content type from headers
    content_type = response.headers.get("Content-Type", "")

    # Get extension from content type
    ext = mimetypes.guess_extension(content_type)

    # If we couldn't determine the extension from headers, use PIL to inspect the image
    if not ext or ext == ".jpe":  # '.jpe' is sometimes returned for jpegs
        img = Image.open(BytesIO(response.content))
        ext = (
            f".{img.format.lower()}" if img.format else ".jpg"
        )  # Default to jpg if format unknown

    # Create the full save path
    save_path = save_dir / f"{stem}{ext}"

    # Save the image
    save_path.write_bytes(response.content)

    return save_path
