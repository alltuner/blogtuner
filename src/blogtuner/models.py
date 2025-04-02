import datetime as dt
import re
import shutil
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List, Optional, Self, cast

import frontmatter  # type: ignore
import git
import mistune
import toml
from dateutil import tz
from dateutil.parser import parse as dateparse
from feedgen.feed import FeedGenerator  # type: ignore
from loguru import logger
from mdformat import text as mdformat
from pydantic import BaseModel, Field, HttpUrl
from slugify import slugify

from .constants import DEFAULT_BLOG_METADATA, DEFAULT_POST_METADATA
from .paths import get_static_file
from .templates import load_template


def move_file_with_git_awareness(source: Path, destination: Path) -> Path:
    """
    Move a file or directory with Git awareness.

    Uses git mv if the file is in a Git repository, otherwise falls back to regular rename.
    """
    source, destination = Path(source), Path(destination)

    if not source.exists():
        raise FileNotFoundError(f"Source path does not exist: {source}")

    if destination.exists():
        raise FileExistsError(f"Destination path already exists: {destination}")

    try:
        # Try to handle with git if applicable
        repo = git.Repo(source.absolute(), search_parent_directories=True)
        rel_source = str(source.absolute().relative_to(repo.working_dir))

        if rel_source in [item[0] for item in repo.index.entries]:
            repo.git.mv(source.absolute(), destination.absolute())
            return destination
    except (git.InvalidGitRepositoryError, git.NoSuchPathError, ValueError):
        pass  # Not a git repo or file not tracked

    # Regular file system move
    source.rename(destination)
    logger.info(f"Renamed file to {destination}")
    return destination


class BlogPost(BaseModel):
    """Represents a blog post with metadata and content."""

    title: str
    slug: str
    pubdate: dt.datetime
    author: Optional[str] = None
    draft: bool = False
    content: str = ""

    @property
    def short_date(self) -> str:
        """Return the publication date in YYYY-MM-DD format."""
        return self.pubdate.strftime("%Y-%m-%d")

    @property
    def filename(self) -> str:
        return f"{self.short_date}-{self.slug}.md"

    @property
    def html_filename(self) -> str:
        """Get the HTML output filename for this post."""
        return f"{self.slug}.html"

    @property
    def metadata(self) -> Dict[str, Any]:
        """Extract metadata for serialization, excluding content."""
        return self.model_dump(
            exclude={"content"},
            exclude_none=True,
            exclude_unset=True,
        )

    @property
    def html_content(self) -> str:
        """Render markdown content as HTML."""
        return str(mistune.html(self.content))

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
        content = mdformat(md_data.content)
        metadata = md_data.metadata

        # Determine publication date
        pubdate = (
            dateparse(str(metadata.get("pubdate")))
            if metadata.get("pubdate")
            else dt.datetime.fromtimestamp(filepath.stat().st_mtime)
        )

        if not metadata.get("pubdate"):
            logger.info(
                f"No publication date found for {filepath}. Using file timestamp."
            )

        # Extract slug from filename or metadata
        date_filename_match = re.match(r"^\d{4}-\d{2}-\d{2}-(.*)", filepath.stem)
        stem = date_filename_match.group(1) if date_filename_match else filepath.stem
        slug = slugify(str(metadata.get("slug", stem)))

        while slug in used_slugs:
            slug = BlogPost.increment_slug_number(slug)

        return cls(
            title=str(metadata.get("title", slug.replace("-", " ").title())),
            slug=slug,
            pubdate=pubdate,
            content=content,
            draft=bool(metadata.get("draft", False)),
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


class BlogConfig(BaseModel):
    """Blog configuration and posts."""

    src_dir: Path
    base_url: Optional[HttpUrl] = None
    base_path: str = "/"
    author: Optional[str] = None
    name: Optional[str] = None
    lang: Optional[str] = None
    url: Optional[str] = None
    footer_text: Optional[str] = None
    timezone: str = Field(default="UTC", alias="tz")
    posts: List[BlogPost] = []

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
        if not config_file.exists():
            logger.info("Blog configuration file not found. Creating a new one.")
            config_file.write_text(toml.dumps(DEFAULT_BLOG_METADATA))

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

            post.save(src_dir=src_dir)
            posts.append(post)

            logger.debug(f"Processed {filepath}")

        # Return configured blog
        return cls(src_dir=src_dir, posts=posts, **toml.load(config_file))

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
        """Get public posts sorted by date descending."""
        return sorted(
            self.get_publishable_posts(), key=lambda post: post.pubdate, reverse=True
        )


class BlogGenerator(BaseModel):
    """Handles generation of blog files from BlogConfig."""

    blog: BlogConfig
    target_dir: Path

    def generate_html_posts(self) -> None:
        """Generate HTML files for all posts."""
        template = load_template("post")
        for post in self.blog.posts:
            output_path = self.target_dir / post.html_filename
            output_path.write_text(template.render(blog=self.blog, post=post))
            logger.info(f"Created HTML file: {output_path}")

    def generate_feed(self) -> None:
        """Generate an Atom feed for the blog."""
        if not self.blog.name or not self.blog.base_url:
            logger.warning("Blog name or URL is not set. Skipping feed generation.")
            return

        feed = FeedGenerator()
        blog_url = self.blog.full_url

        # Set feed properties
        feed.id(blog_url)
        feed.title(cast(str, self.blog.name))
        if self.blog.author:
            feed.author({"name": self.blog.author})
        if self.blog.lang:
            feed.language(self.blog.lang)

        # Add feed links
        feed.link(href=blog_url, rel="alternate")
        feed.link(href=f"{blog_url}feed.xml", rel="self")

        # Add entries for all public posts
        tz_info = tz.gettz(self.blog.timezone)
        for post in self.blog.sorted_public_posts:
            entry_url = f"{blog_url}{post.html_filename}"
            entry = feed.add_entry()
            entry.id(entry_url)
            entry.title(post.title)
            entry.link(href=entry_url)
            entry.content(post.html_content, type="html")
            entry.published(post.pubdate.replace(tzinfo=tz_info))

        # Write feed file
        feed_path = self.target_dir / "feed.xml"
        feed_path.write_text(feed.atom_str(pretty=True).decode("utf-8"))
        logger.info(f"Created XML feed: {feed_path}")

    def generate_index(self) -> None:
        """Generate the main index.html file."""
        index_path = self.target_dir / "index.html"
        index_path.write_text(load_template("list").render(blog=self.blog))
        logger.info(f"Created blog index HTML file: {index_path}")

    def copy_assets(self) -> None:
        """Copy CSS and other static assets to the output directory."""
        shutil.copy(get_static_file("bundle.css"), self.target_dir / "bundle.css")
        logger.info("Copied CSS assets")

    def generate_site(self) -> None:
        """Generate the complete blog site."""
        logger.info(f"Building site from {self.blog.src_dir} to {self.target_dir}")

        self.copy_assets()
        self.generate_html_posts()
        self.generate_index()
        self.generate_feed()
        logger.info("Blog site generation complete")
