import datetime as dt
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List, Optional, Self

import toml
from pydantic import BaseModel, Field, HttpUrl

from blogtuner.core.post import BlogPost
from blogtuner.utils.git import move_file_with_git_awareness
from blogtuner.utils.images import BlogImage, ImageFile, create_webp_image_from_bytes
from blogtuner.utils.logs import logger


# Define default post metadata
DEFAULT_BLOG_METADATA: Dict[str, Any] = {
    "base_url": None,
    "base_path": "/",
    "author": "Anonymous",
    "name": "My Blog Powered by BlogTuner",
    "lang": "en",
    "tz": "UTC",
    "footer_text": "Powered by <a href='https://github.com/alltuner/blogtuner'>BlogTuner</a>",
    "links": {
        "BlogTuner": "https://github.com/alltuner/blogtuner",
        "All Tuner Labs": "https://alltuner.com/",
    },
    "twitter_metadata": {
        "site": None,
        "creator": None,
    },
    "description": "A blog powered by BlogTuner",
    "image_checksum": None,
}


class BlogConfig(BaseModel):
    """Blog configuration and posts."""

    src_dir: Path
    base_url: Optional[HttpUrl] = None
    base_path: str = "/"
    author: Optional[str] = None
    name: Optional[str] = None
    lang: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    footer_text: Optional[str] = None
    timezone: str = Field(default="UTC", alias="tz")
    posts: List[BlogPost] = []
    css: Optional[str] = None
    links: Optional[Dict[str, HttpUrl]] = None

    twitter_metadata: Optional[Dict[str, str | None]] = None
    image_checksum: Optional[str] = None
    image: Optional[BlogImage] = None

    @property
    def used_slugs(self) -> set[str]:
        """Get a set of all used slugs."""
        return {post.slug for post in self.posts}

    def unpublish_post(self, slug: str) -> None:
        """Unpublish a post by slug."""
        for post in self.posts:
            if post.slug == slug:
                post.draft = True
                post.save(src_dir=self.src_dir)
                logger.info(f"Unpublished post {slug}")
                return

        logger.warning(f"Post with slug {slug} not found")

    def publish_post(self, slug: str) -> None:
        """Publish a post by slug."""
        for post in self.posts:
            if post.slug == slug:
                post.draft = False
                post.save(src_dir=self.src_dir)
                logger.info(f"Published post {slug}")
                return

        logger.warning(f"Post with slug {slug} not found")

    def delete_post(self, slug: str) -> None:
        """Delete a post by slug."""
        logger.warning(
            "This is a destructive operation, for safety, we don't remove files from git even if the source directory is revision controlled."
        )
        for post in self.posts:
            if post.slug == slug:
                filepath = self.src_dir / post.filename
                if filepath.exists():
                    filepath.unlink()
                    logger.info(f"Deleted post {slug}")
                return

        logger.warning(f"Post with slug {slug} not found")

    @classmethod
    def from_directory(cls, src_dir: Path) -> Self:
        """Load blog configuration and posts from a source directory."""
        # Load or create blog configuration
        config_file = src_dir / "blog.toml"

        # Load blog configuration
        configuration = DEFAULT_BLOG_METADATA.copy()
        if config_file.exists():
            configuration.update(toml.load(config_file))

        blog_artwork_file = src_dir / "blog_artwork.webp"
        blog_image = None
        if blog_artwork_file.exists():
            blog_image = ImageFile.from_filepath(blog_artwork_file)
        elif image := ImageFile.from_path(src_dir, "blog"):
            blog_artwork_file.write_bytes(create_webp_image_from_bytes(image.bytes_))
            blog_image = ImageFile.from_filepath(blog_artwork_file)

        configuration["image_checksum"] = (
            f"{blog_image.checksum}" if blog_image else None
        )
        config_file.write_text(toml.dumps(configuration))

        # Process posts
        posts: list[BlogPost] = []
        used_slugs: set[str] = set()

        for filepath in src_dir.iterdir():
            if filepath.suffix != ".md":
                logger.debug(f"Skipping non-Markdown file {filepath}")
                continue

            post = BlogPost.from_markdown_file(filepath=filepath, used_slugs=used_slugs)

            used_slugs.add(post.slug)

            if post.filename != filepath.name:
                move_file_with_git_awareness(filepath, src_dir / post.filename)

            if image := ImageFile.from_path(src_dir, {post.stem, post.slug}):
                if image.filepath.stem != post.stem:
                    move_file_with_git_awareness(
                        image.filepath,
                        src_dir / f"{post.stem}{image.filepath.suffix}",
                    )
                    logger.info(
                        f"Moved image from {image.filepath} to {src_dir / f'{post.stem}{image.filepath.suffix}'}"
                    )

            post.image = image

            post.save(src_dir=src_dir)
            posts.append(post)

            logger.debug(f"Processed {filepath}")

        blog_data = configuration.copy()
        if blog_image:
            blog_data["image"] = blog_image

        # Return configured blog
        return cls(src_dir=src_dir, posts=posts, **blog_data)

    def import_markdown_file(self, filepath: Path) -> None:
        """Import a Markdown file into the blog."""
        logger.info(f"Importing {filepath} into blog")

        post = BlogPost.from_markdown_file(
            filepath=filepath,
            used_slugs=self.used_slugs,
        )
        post.save(src_dir=self.src_dir)

    @property
    def footer(self) -> Optional[str]:
        """Get the footer text if available."""
        return str(self.footer_text) if self.footer_text else None

    @property
    def image_url(self) -> Optional[str]:
        """Get the URL of the blog image if available."""
        if not self.image:
            logger.warning("Blog image is not set")
            return None

        return f"{self.full_url}{self.image_checksum}.webp"

    @property
    def relative_thumbnail_image_url(self) -> Optional[str]:
        """Get the URL of the blog image if available."""
        if not self.image:
            logger.warning("Blog image is not set")
            return None

        return f"{self.base_path}{self.image_checksum}.thumbnail.webp"

    @property
    def full_url(self) -> str:
        """Construct the full blog URL from base URL and path."""
        if not self.base_url:
            logger.warning("Base URL is not set")
            return self.base_path

        base = str(self.base_url).rstrip("/")
        path = self.base_path.lstrip("/")
        return f"{base}/{path}" if path else base

    def get_public_posts(self) -> List[BlogPost]:
        """Filter out draft posts."""
        return [post for post in self.posts if not post.draft]

    @property
    def public_posts(self) -> List[BlogPost]:
        """Get public posts."""
        return self.get_public_posts()

    def get_publishable_posts(self) -> List[BlogPost]:
        """Filter out posts that are scheduled for the future and drafts."""
        now = dt.datetime.now()
        return [post for post in self.get_public_posts() if post.pubdate <= now]

    def get_sorted_posts(self, reverse: bool = True) -> List[BlogPost]:
        """Sort posts by publication date."""
        return sorted(self.posts, key=lambda post: post.pubdate, reverse=reverse)

    @cached_property
    def sorted_public_posts(self) -> List[BlogPost]:
        """Get public posts sorted by pinned status first, then by date descending."""
        publishable_posts = self.get_publishable_posts()
        return sorted(
            publishable_posts,
            key=lambda post: (
                not getattr(post, "pinned", False),
                -post.pubdate.timestamp(),
            ),
        )
