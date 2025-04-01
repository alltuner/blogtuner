from pathlib import Path

from .models import BlogConfig, BlogGenerator
from .paths import setup_target_dir


def build_site(target_dir: Path, blog: BlogConfig) -> None:
    """Build the site using the provided blog writer."""
    setup_target_dir(target_dir)
    blog_writer = BlogGenerator(blog=blog, target_dir=target_dir)
    blog_writer.generate_site()
