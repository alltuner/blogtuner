# BlogTuner

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Blog every day, no excuses.

BlogTuner is a damn simple static blog generator that converts Markdown files to a super basic HTML blog with zero fuss. No complex configurations, no steep learning curves—just write and publish.

## Features

- **Dead Simple**: Convert a directory of Markdown files to HTML—that's it
- **Lightning Fast**: Generates your entire site in milliseconds
- **No Excuses**: Removes all barriers to daily blogging
- **RSS Ready**: Automatically generates an Atom feed for your readers
- **Markdown Power**: Write in Markdown, publish as HTML
- **Smart Defaults**: Sensible defaults with minimal configuration
- **Draft Support**: Mark posts as drafts with frontmatter or naming convention
- **Date Flexibility**: Specify publication dates in frontmatter or rely on file timestamps
- **File Organization**: Automatic file renaming to standard format (YYYY-MM-DD-slug.md)
- **GitHub Pages Ready**: Generate static HTML perfect for free hosting

## Motivation

Some folks such as Simon Willison have convinced me to start blogging my thoughts. I wanted to keep things simple—just a dumb set of markdown files should be enough to create a super simple HTML blog.

Even with great tools like Zola, Hugo, and Pelican available, they felt too complicated for what I needed. I wanted the minimal expression of simplicity. Hence, BlogTuner was born.

The idea is to keep your markdown files in a repo, generate HTML with BlogTuner, and deploy to a service like GitHub Pages. As simple as that.

## Installation

The recommended way to use BlogTuner is via `uvx`:

```bash
uvx blogtuner build source_dir target_dir
```

If you prefer to install it:

```bash
uv pip install blogtuner
```

## Usage

### Basic Usage

```bash
# Create a new blog directory
mkdir myblog
cd myblog

# Create your first post
echo "# Hello World" > first-post.md

# Generate your blog
uvx blogtuner build . _site
```

### File Naming and Organization

Blogtuner will automatically rename your files to follow the pattern `YYYY-MM-DD-slug.md`.

If a date isn't specified in the frontmatter, it will use the file's modification time.

### Frontmatter

Posts can include TOML frontmatter at the beginning of the file (if you don't include it it will be generated during the first run):

```markdown
+++
title = "My Awesome Post"
pubdate = "2024-03-28"
draft = false
slug = "custom-slug"  # Optional, defaults to filename
+++

# My Awesome Post

Content goes here...
```

### Blog Configuration

Create a `blog.toml` in your source directory (it will be created on the first run if you are lazy like me):

```toml
name = "My Awesome Blog"
author = "Your Name"
base_url = "https://yourdomain.com"
base_path = "/"
lang = "en"
tz = "UTC"
footer_text = "Powered by <a href='https://github.com/alltuner/blogtuner'>Blogtuner</a>"
```

## Features in Detail

### Post Processing

- **Automatic Metadata**: Extract frontmatter from posts or use defaults
- **Date Handling**: Parse dates from frontmatter or use file modification time
- **Drafts**: Posts marked as drafts won't appear in the index or feed
- **File Normalization**: Files are automatically renamed to YYYY-MM-DD-slug.md format

### Site Generation

- **HTML Generation**: Clean, simple HTML for each post and index
- **Feed Generation**: Atom feed for syndication
- **CSS Bundling**: Simple, clean CSS included automatically
- **Fast Processing**: Efficient processing even for large numbers of posts

## Example Workflow

1. Write posts in Markdown with optional TOML frontmatter
2. Run Blogtuner to generate HTML and the Atom feed
3. Push HTML to GitHub Pages or your hosting service
4. Repeat daily (no excuses!)

## License

MIT
