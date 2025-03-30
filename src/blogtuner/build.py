import datetime as dt
import re
import shutil
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Self

import frontmatter  # type: ignore
import git
import mistune
import toml
from dateutil import tz
from dateutil.parser import parse as dateparse
from feedgen.feed import FeedGenerator  # type: ignore
from jinja2 import Environment, FileSystemLoader, Template
from mdformat import text as mdformat
from pydantic import BaseModel, HttpUrl
from slugify import slugify

from . import logger


with as_file(files("blogtuner.data").joinpath("templates")) as template_path:
    jinja_env = Environment(
        autoescape=True,
        loader=FileSystemLoader(template_path),
    )
    jinja_env.filters["date"] = lambda value, format=None: value.strftime(
        format if format else "%Y-%m-%d"
    )


def _get_static_file(name: str) -> Path:
    with as_file(files("blogtuner.data").joinpath("statics")) as static_path:
        return static_path / name


def smart_move(source_path: Path, destination_path: Path) -> Path:
    """
    Move a file or directory from source_path to destination_path.

    If the file is part of a Git repository, uses git mv for the operation.
    Otherwise, uses regular file system rename.

    Args:
        source_path: A Path object pointing to the source file/directory
        destination_path: A Path object pointing to the desired destination

    Raises:
        FileExistsError: If destination_path already exists
        FileNotFoundError: If source_path doesn't exist

    Returns:
        Path: The destination path after successful move
    """
    # Ensure paths are Path objects
    source_path = Path(source_path)
    destination_path = Path(destination_path)

    # Check if source exists
    if not source_path.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_path}")

    # Check if destination already exists
    if destination_path.exists():
        raise FileExistsError(f"Destination path already exists: {destination_path}")

    # Try to determine if source is in a git repository
    try:
        # Get absolute paths for reliability
        source_abs = source_path.absolute()
        dest_abs = destination_path.absolute()

        # Find the git repo that might contain the source
        repo = git.Repo(source_abs, search_parent_directories=True)

        # Check if the file is tracked by git
        # Get relative path within the repo
        rel_source = str(source_abs.relative_to(repo.working_dir))

        # Check if the file is tracked
        tracked_files = [item[0] for item in repo.index.entries]
        if rel_source in tracked_files:
            # Use git mv for the operation
            repo.git.mv(source_abs, dest_abs)
            return destination_path
    except (git.InvalidGitRepositoryError, git.NoSuchPathError, ValueError):
        # Not a git repo or file not tracked - will fall back to regular move
        pass

    # If we got here, either it's not a git object or an error occurred
    # Fall back to regular rename
    source_path.rename(destination_path)
    return destination_path


# Define default post metadata
DEFAULT_POST_METADATA: Dict[str, Any] = {}
DEFAULT_BLOG_METADATA: Dict[str, Any] = {
    "base_url": None,
    "base_path": "/",
    "author": "Anonymous",
    "name": "My Blog",
    "lang": "en",
    "tz": "UTC",
    "footer_text": "Powered by <a href='https://github.com/alltuner/blogtuner'>BlogTuner</a>",
}


class FileData(BaseModel):
    """Data model for file content and metadata."""

    file: Path
    metadata: Dict[str, Any]
    content: str

    @property
    def slug(self) -> str:
        match = re.match(r"^\d{4}-\d{2}-\d{2}-(.*)", self.file.stem)
        stem = match.group(1) if match else self.file.stem

        slug = str(self.metadata.get("slug", stem))
        return slugify(slug)

    @property
    def title(self) -> str:
        return str(self.metadata.get("title", self.slug.replace("-", " ").title()))

    @property
    def pubdate(self) -> dt.datetime:
        if pubdate := self.metadata.get("pubdate"):
            return dateparse(str(pubdate))

        logger.info(f"No publication date found for {self.file}. Using file timestamp.")
        return dt.datetime.fromtimestamp(self.file.stat().st_mtime)

    @classmethod
    def from_file(cls, file: Path) -> Self:
        data = frontmatter.loads(file.read_text(), **DEFAULT_POST_METADATA)
        file_data = cls(
            file=file, metadata=data.metadata, content=mdformat(data.content)
        )

        file_data.normalize_file_name()
        return file_data

    @property
    def short_pubdate(self) -> str:
        return self.pubdate.strftime("%Y-%m-%d")

    def normalize_file_name(self) -> None:
        new_file = self.file.with_name(f"{self.short_pubdate}-{self.slug}.md")
        if new_file == self.file:
            logger.debug(f"File name {self.file} is already normalized")
            return

        if new_file.exists() and not new_file.is_file():
            logger.error(f"Target file {new_file} already exists, and it is not a file")
            return

        self.file = smart_move(self.file, new_file)
        logger.info(f"Renamed file to {self.file}")

    def write_file(self, defaults: dict) -> None:
        self.file.write_text(
            frontmatter.dumps(
                post=frontmatter.Post(
                    content=self.content,
                    **{
                        **self.metadata,
                        **defaults,
                    },
                ),
                handler=frontmatter.TOMLHandler(),
            )
        )


class Post(BaseModel):
    """Data model representing a blog post."""

    title: str
    slug: str
    pubdate: dt.datetime
    author: Optional[str] = None
    draft: bool = False
    content: str = ""

    @classmethod
    def from_file_data(cls, file_data: FileData) -> Self:
        return cls(
            title=file_data.title,
            slug=file_data.slug,
            pubdate=file_data.pubdate,
            content=file_data.content,
            draft=bool(file_data.metadata.get("draft", False)),
        )

    @property
    def html_file_name(self) -> str:
        return f"{self.slug}.html"

    @property
    def metadata(self) -> Dict[str, Any]:
        return self.model_dump(
            exclude={"content"},
            exclude_none=True,
            exclude_unset=True,
        )

    @property
    def html(self) -> str:
        """Converts the markdown content to html."""
        return str(mistune.html(self.content))


class Blog(BaseModel):
    base_url: Optional[HttpUrl] = None
    base_path: str = "/"

    author: Optional[str] = None
    name: Optional[str] = None
    lang: Optional[str] = None
    url: Optional[str] = None

    footer_text: Optional[str] = None

    tz: str = "UTC"

    posts: List[Post] = []

    @property
    def footer(self) -> str | None:
        """Construct the footer text."""
        return str(self.footer_text) if self.footer_text else None

    @property
    def blog_url(self) -> str:
        """Construct the blog URL from base URL and path."""
        if not self.base_url:
            logger.warning("Base URL is not set")
            return self.base_path

        return str(self.base_url) + self.base_path.lstrip("/")

    def public(self) -> "Blog":
        """Filter out draft posts."""
        return self.model_copy(
            update={
                "posts": list(
                    filter(
                        lambda post: not post.draft,
                        self.posts,
                    )
                )
            }
        )

    def publishable(self) -> "Blog":
        """Filter out posts that are scheduled for the future and drafts."""
        return self.model_copy(
            update={
                "posts": list(
                    filter(
                        lambda post: post.pubdate <= dt.datetime.now(),
                        self.public().posts,
                    )
                )
            }
        )

    def sorted(self) -> "Blog":
        """Sort posts by publication date in descending order."""
        return self.model_copy(
            update={
                "posts": sorted(self.posts, key=lambda post: post.pubdate, reverse=True)
            }
        )

    @property
    def public_posts(self) -> List[Post]:
        """Get public posts."""
        return self.publishable().sorted().posts


class BlogWriter(BaseModel):
    """Data model for writing blog files."""

    blog: Blog
    target_dir: Path

    def write_html_posts(self) -> None:
        template = load_template("post")
        for post in self.blog.posts:
            target_html_file = self.target_dir / post.html_file_name
            target_html_file.write_text(template.render(blog=self.blog, post=post))
            logger.info(f"Created HTML file: {target_html_file}")

    def generate_feed_content(self) -> None:
        """Generate an Atom feed from a blog object.

        Args:
            blog: Blog object with metadata and posts

        Returns:
            Atom feed XML content
        """

        feed: FeedGenerator = FeedGenerator()
        feed.id(self.blog.blog_url)
        feed.title(self.blog.name)
        if self.blog.author:
            feed.author({"name": self.blog.author})
        if self.blog.lang:
            feed.language(self.blog.lang)

        feed.link(href=self.blog.blog_url, rel="alternate")
        feed.link(href=self.blog.blog_url + "feed.xml", rel="self")

        for post in self.blog.posts:
            target_link = str(self.blog.blog_url) + post.html_file_name

            fe = feed.add_entry()
            fe.id(target_link)
            fe.title(post.title)
            fe.link(href=target_link)
            fe.content(post.html, type="html")
            fe.published(post.pubdate.replace(tzinfo=tz.gettz(self.blog.tz)))

        target_feed_xml_file = self.target_dir / "feed.xml"
        target_feed_xml_file.write_text(feed.atom_str(pretty=True).decode("utf-8"))

        logger.info(f"Created XML feed: {target_feed_xml_file}")

    def create_index_file(self) -> None:
        template = load_template("list")

        target_html_file = self.target_dir / "index.html"
        target_html_file.write_text(template.render(blog=self.blog))
        logger.info(f"Created blog index HTML file: {target_html_file}")

    def copy_css(self) -> None:
        """Copy CSS files to the target directory."""
        shutil.copy(_get_static_file("bundle.css"), self.target_dir / "bundle.css")

    def generate(self) -> None:
        """Generate the blog site by writing HTML files and feeds."""
        self.copy_css()
        self.write_html_posts()
        self.create_index_file()

        if not self.blog.name or not self.blog.base_url:
            logger.warning("Blog name or URL is not set. Skipping feed generation.")

            return

        self.generate_feed_content()


def load_template(name: str) -> Template:
    """Load a template by name.

    Args:
        name: Template name without extension

    Returns:
        Jinja2 template object
    """
    return jinja_env.get_template(f"{name}.html.jinja")


def build_site(source_dir: Path, target_dir: Path) -> None:
    """Build a static site from markdown files.

    Args:
        source_dir: Directory containing markdown files
        target_dir: Directory to output processed files
    """
    # Validate directories
    if not source_dir.exists() or not source_dir.is_dir():
        logger.error(f"Source directory {source_dir} not found or not a directory")
        return

    if not target_dir.exists():
        target_dir.mkdir(parents=True)
        logger.info(f"Created target directory {target_dir}")
    elif not target_dir.is_dir():
        logger.error(f"Target directory {target_dir} is not a directory")
        return

    blog_config_file = source_dir / "blog.toml"
    if not blog_config_file.exists():
        blog_config_file.write_text(toml.dumps(DEFAULT_BLOG_METADATA))

    BlogWriter(
        blog=Blog(
            posts=list(process_markdown_files(source_dir)),
            **toml.load(blog_config_file),
        ),
        target_dir=target_dir,
    ).generate()

    logger.info(f"Building site from {source_dir} to {target_dir}")


def process_markdown_files(source_dir: Path) -> Generator[Post, Any, None]:
    # Process markdown files
    for file in source_dir.iterdir():
        if file.suffix != ".md":
            logger.debug(f"Skipping non-Markdown file {file}")
            continue

        # Extract and process file data
        file_data = FileData.from_file(file)

        post = Post.from_file_data(file_data)
        yield post

        # Update source file with normalized metadata
        file_data.write_file(post.metadata)
        logger.debug(f"Processed {file}")
