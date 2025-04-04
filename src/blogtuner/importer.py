from datetime import datetime
from pathlib import Path

import dateutil.parser
from rich import print
from slugify import slugify
from substack_api import Newsletter  # type: ignore

from .llm import get_markdown_from_substack
from .logs import logger
from .models import BlogPost, ImageFile


def date_to_dt(date_str: str) -> datetime:
    return dateutil.parser.isoparse(date_str).replace(tzinfo=None)


def import_substack_posts(
    substack_url: str,
    used_slugs: set[str],
    src_dir: Path,
):
    print(f"Importing posts from {substack_url}...")

    newsletter = Newsletter(substack_url)
    try:
        for post in newsletter.get_posts():
            metadata = post.get_metadata()
            original_pubdate = metadata.get(
                "updated_at", metadata.get("post_date", None)
            )
            title = metadata.get("title", None)

            slug = slugify(metadata.get("slug", title))
            while slug in used_slugs:
                slug = BlogPost.increment_slug_number(slug)

            post = BlogPost(
                title=title,
                slug=slug,
                content=get_markdown_from_substack(
                    html=post.get_content(),
                    title=title,
                ),
                original_href=metadata.get("canonical_url", None),
                original_pubdate=date_to_dt(original_pubdate),
                pubdate=date_to_dt(original_pubdate),
                draft=False,
                oneliner=metadata.get("description", None),
                tags=[t["name"] for t in metadata.get("postTags", [])],
            )

            if image_url := metadata.get("cover_image", None):
                post.image = ImageFile.from_url(
                    url=image_url, stem=post.stem, save_dir=src_dir
                )

            used_slugs.add(slug)
            post.save(src_dir)

    except Exception as e:
        logger.error(f"An error occurred while fetching posts: {e}")
