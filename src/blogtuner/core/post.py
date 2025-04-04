import datetime as dt
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Self

import frontmatter  # type: ignore
from dateutil.parser import parse as dateparse
from pydantic import BaseModel, HttpUrl, field_serializer
from slugify import slugify

from blogtuner.rendering.markdown import format_markdown, to_html
from blogtuner.utils.images import PostImage


DEFAULT_POST_METADATA: Dict[str, Any] = {}


class BlogPost(BaseModel):
    """Represents a blog post with metadata and content."""

    title: str
    slug: str
    pubdate: dt.datetime
    author: Optional[str] = None
    draft: bool = False
    content: str = ""

    # Post images
    image: Optional[PostImage] = None

    # Pinning (pinned posts will be displayed first)
    pinned: bool = False

    # Extra metadata fields
    tags: List[str] = []
    oneliner: Optional[str] = None
    description: Optional[str] = None
    llm_image_prompt: Optional[str] = None

    # Original publication
    original_href: Optional[HttpUrl] = None
    original_pubdate: Optional[dt.datetime] = None

    @field_serializer("original_href")
    def serialize_original_href(self, value: Optional[HttpUrl]) -> Optional[str]:
        """Serialize original_href to a string."""
        return str(value) if value else None

    @property
    def thumbnail(self) -> str | None:
        if self.image and self.image.checksum:
            return f"{self.image.checksum}.thumbnail.webp"

        return None

    @property
    def short_date(self) -> str:
        """Return the publication date in YYYY-MM-DD format."""
        return self.pubdate.strftime("%Y-%m-%d")

    @property
    def filename(self) -> str:
        return f"{self.stem}.md"

    @property
    def stem(self) -> str:
        """Get the stem of the filename."""
        return f"{self.short_date}-{self.slug}"

    @property
    def html_filename(self) -> str:
        """Get the HTML output filename for this post."""
        return f"{self.slug}.html"

    @property
    def metadata(self) -> Dict[str, Any]:
        """Extract metadata for serialization, excluding content."""
        return self.model_dump(
            exclude={"content": True, "image": {"bytes_"}},
            exclude_none=True,
            exclude_unset=True,
        )

    @property
    def html_content(self) -> str:
        """Render markdown content as HTML."""
        return str(to_html(self.content))

    def save(self, src_dir: Path) -> None:
        """Write normalized metadata back to file."""

        filepath = src_dir / self.filename
        filepath.write_text(
            frontmatter.dumps(
                post=frontmatter.Post(content=self.content, **self.metadata),
                handler=frontmatter.TOMLHandler(),
            )
        )

    @classmethod
    def from_markdown_file(cls, filepath: Path, used_slugs: set[str]) -> Self:
        # Parse frontmatter and content
        md_data = frontmatter.loads(filepath.read_text(), **DEFAULT_POST_METADATA)
        metadata = md_data.metadata

        # Determine publication date
        metadata["pubdate"] = (
            dateparse(str(metadata.get("pubdate")))
            if metadata.get("pubdate")
            else dt.datetime.fromtimestamp(filepath.stat().st_mtime)
        )

        # Extract slug from filename or metadata
        date_filename_match = re.match(r"^\d{4}-\d{2}-\d{2}-(.*)", filepath.stem)
        stem = date_filename_match.group(1) if date_filename_match else filepath.stem
        slug = slugify(str(metadata.get("slug", stem)))

        while slug in used_slugs:
            slug = BlogPost.increment_slug_number(slug)

        metadata["slug"] = slug
        metadata["title"] = metadata.get("title", slug.replace("-", " ").title())
        metadata["draft"] = metadata.get("draft", False)

        return cls(
            content=format_markdown(md_data.content),
            **metadata,
        )

    @staticmethod
    def increment_slug_number(slug) -> str:
        """Increment the numeric suffix of a slug or add -1 if no suffix exists."""
        match = re.match(r"^(.*?)(-\d+)?$", slug)
        if not match:
            return f"{slug}-1"

        base_slug, num_suffix = match.groups()
        if not num_suffix:
            return f"{base_slug}-1"

        return f"{base_slug}-{int(num_suffix[1:]) + 1}"
