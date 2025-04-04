import hashlib
import io
from functools import cached_property
from pathlib import Path
from typing import Optional, Self

from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, computed_field

from blogtuner.utils.logs import logger
from blogtuner.utils.paths import save_image


class BlogImage(BaseModel):
    bytes_: bytes = b""
    suffix: Optional[str] = ""

    @computed_field  # type: ignore[misc]
    @cached_property
    def checksum(self) -> str | None:
        """Calculate the checksum of the image bytes."""
        return hashlib.sha256(self.bytes_).hexdigest()[:10] if self.bytes_ else None

    @cached_property
    def thumbnail(self) -> bytes:
        return create_web_thumbnail_from_bytes(self.bytes_)

    @cached_property
    def image(self) -> bytes:
        return create_webp_image_from_bytes(self.bytes_)

    @property
    def image_length(self) -> int:
        return len(self.image)


PostImage = BlogImage


class ImageFile(BlogImage):
    filepath: Path

    @classmethod
    def from_path(cls, src_dir: Path, stems: str | set[str]) -> Self | None:
        """Load image file from the specified path."""
        if isinstance(stems, str):
            stems = {stems}

        for stem in stems:
            logger.debug(f"Checking for image file with stem: {stem} in {src_dir}")
            image_file = find_image_file(src_dir, stem)
            if image_file:
                return cls(
                    bytes_=image_file.read_bytes(),
                    filepath=image_file,
                    suffix=image_file.suffix,
                )

        return None

    @classmethod
    def from_filepath(cls, filepath: Path) -> Self:
        """Load image file from the specified path."""
        if not filepath.exists():
            raise FileNotFoundError(f"File {filepath} does not exist.")

        return cls(
            bytes_=filepath.read_bytes(),
            filepath=filepath,
            suffix=filepath.suffix,
        )

    @classmethod
    def from_url(cls, url: str, stem: str, save_dir: Path) -> Self:
        """Load image from a URL."""

        image_file = save_image(url=url, stem=stem, save_dir=save_dir)
        return cls(
            bytes_=image_file.read_bytes(),
            filepath=image_file,
            suffix=image_file.suffix,
        )


SUPPORTED_EXTENSIONS = (
    ".webp",  # WebP images
    ".jpg",
    ".jpeg",  # JPEG images
    ".png",  # PNG images
    ".gif",  # GIF images
    ".tiff",
    ".tif",  # TIFF images
)


def find_image_file(directory: Path, stem: str) -> Path | None:
    """Find image files in a directory with specified extensions."""
    for ext in SUPPORTED_EXTENSIONS:
        image_file = directory / f"{stem}{ext}"
        if image_file.exists():
            try:
                # Attempt to open the image with PIL
                with Image.open(image_file) as img:
                    # Accessing img.format verifies the image is valid
                    # without loading the entire image into memory
                    if img.format:
                        return image_file
            except (UnidentifiedImageError, OSError, IOError):
                # File exists but can't be opened as an image by PIL
                logger.info(f"File {image_file} is not a valid image.")
                continue

    return None


def create_web_thumbnail_from_bytes(data: bytes, w: int = 128, h: int = 128) -> bytes:
    """
    Create a thumbnail image from bytes.

    Args:
        data: The image data in bytes
        w: Desired thumbnail width (default: 128)
        h: Desired thumbnail height (default: 128)

    Returns:
        Thumbnail image data in WebP format as bytes
    """
    # Create an image object from bytes
    img = Image.open(io.BytesIO(data))

    # Convert to RGB mode if needed (in case it's RGBA or other mode)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Create thumbnail
    img.thumbnail((w, h), Image.Resampling.LANCZOS)

    # Save as WebP to bytes
    output = io.BytesIO()
    img.save(output, format="WEBP", quality=85)

    return output.getvalue()


def create_webp_image_from_bytes(
    data: bytes, maxw: int = 1024, maxh: int = 768
) -> bytes:
    """
    Create a WebP image from bytes with maximum dimensions.

    Args:
        data: The image data in bytes
        maxw: Maximum width (default: 1024)
        maxh: Maximum height (default: 768)

    Returns:
        Resized image data in WebP format as bytes
    """
    # Create an image object from bytes
    img = Image.open(io.BytesIO(data))

    # Convert to RGB mode if needed
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Calculate dimensions while maintaining aspect ratio
    width, height = img.size
    ratio = min(maxw / width, maxh / height)

    # Only resize if the image is larger than max dimensions
    if ratio < 1:
        new_size = (int(width * ratio), int(height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # Save as WebP to bytes
    output = io.BytesIO()
    img.save(output, format="WEBP", quality=90)

    return output.getvalue()
