import shutil
from pathlib import Path
from typing import cast

from dateutil import tz
from feedgen.feed import FeedGenerator  # type: ignore
from pydantic import BaseModel

from blogtuner.core.blog import BlogConfig
from blogtuner.rendering.markdown import css_styles
from blogtuner.rendering.templates import load_template
from blogtuner.utils.logs import logger
from blogtuner.utils.paths import get_static_file


class BlogGenerator(BaseModel):
    """Handles generation of blog files from BlogConfig."""

    blog: BlogConfig
    target_dir: Path

    def generate_html_posts(self) -> None:
        """Generate HTML files for all posts."""
        template = load_template("post")
        target_dir = self.target_dir
        for post in self.blog.posts:
            html_file = target_dir / post.html_filename
            html_file.write_text(template.render(blog=self.blog, post=post))
            logger.info(f"Created HTML file: {html_file} for post {post.slug}")

            if post.image and post.image.checksum is not None:
                thumbnail_file = target_dir / f"{post.image.checksum}.thumbnail.webp"
                if not thumbnail_file.exists():
                    thumbnail_file.write_bytes(post.image.thumbnail)
                    logger.info(
                        f"Created Thumbnail {thumbnail_file} for post {post.slug}"
                    )

                image_file = target_dir / f"{post.image.checksum}.webp"
                if not image_file.exists():
                    image_file.write_bytes(post.image.image)
                    logger.info(f"Created Image {image_file} for post {post.slug}")

        logger.info("HTML posts generation complete.")

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

        feed.description(
            self.blog.description if self.blog.description else self.blog.name
        )

        # Add feed links
        feed.link(href=blog_url, rel="alternate")
        feed.link(href=f"{blog_url}feed.xml", rel="self")

        # Add entries for all public posts
        tz_info = tz.gettz(self.blog.timezone)
        for post in self.blog.sorted_public_posts:
            entry_url = f"{blog_url}{post.html_filename}"
            entry = feed.add_entry()
            entry.id(entry_url)
            if post.oneliner:
                entry.description(post.oneliner)
            entry.title(post.title)
            if post.tags:
                for tag in post.tags:
                    entry.category(term=tag)
            entry.link(href=entry_url)

            if post.image and post.image.checksum:
                image_url = f"{blog_url}{post.image.checksum}.webp"
                entry.enclosure(
                    url=image_url, length=post.image.image_length, type="image/webp"
                )

            entry.content(post.html_content, type="html")
            entry.published(post.pubdate.replace(tzinfo=tz_info))

        # Write feed file
        feed_path = self.target_dir / "feed.xml"
        feed_path.write_text(feed.rss_str(pretty=True).decode("utf-8"))
        logger.info(f"Created XML feed: {feed_path}")

    def generate_index(self) -> None:
        """Generate the main index.html file."""
        index_path = self.target_dir / "index.html"
        index_path.write_text(load_template("list").render(blog=self.blog))
        logger.info(f"Created blog index HTML file: {index_path}")

    def copy_blog_image(self) -> None:
        if self.blog.image:
            final_image = self.target_dir / f"{self.blog.image.checksum}.webp"
            thumbnail_image = (
                self.target_dir / f"{self.blog.image.checksum}.thumbnail.webp"
            )
            if not final_image.exists():
                final_image.write_bytes(self.blog.image.bytes_)

            if not thumbnail_image.exists():
                thumbnail_image.write_bytes(self.blog.image.thumbnail)

            logger.info(f"Copied blog image to {final_image}")

    def copy_assets(self) -> None:
        """Copy CSS and other static assets to the output directory."""
        extra_css = self.target_dir / "extra.css"
        extra_css.write_text(css_styles)
        shutil.copy(get_static_file("bundle.css"), self.target_dir / "bundle.css")
        logger.info("Copied CSS assets")

    def generate_site(self) -> None:
        """Generate the complete blog site."""
        logger.info(f"Building site from {self.blog.src_dir} to {self.target_dir}")

        self.copy_assets()
        self.copy_blog_image()
        self.generate_html_posts()
        self.generate_index()
        self.generate_feed()
        logger.info("Blog site generation complete")
