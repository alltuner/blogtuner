# BlogTuner 🎵

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Blog every damn day, no excuses.

BlogTuner is a ridiculously simple static blog generator that converts Markdown files to HTML with zero fuss. No complex configurations, no steep learning curves—just write and publish.

## ✨ Features

- **Dead Simple**: Convert Markdown to HTML—that's it
- **Lightning Fast** ⚡: Generates your entire site in milliseconds
- **No Excuses** 🙅: Removes all barriers to daily blogging
- **RSS Ready** 📡: Automatically generates a feed for your blog
- **Markdown Power** 📝: Write in Markdown, publish as HTML
- **Smart Defaults** 🧠: Sensible defaults with minimal configuration
- **Draft Support** 📋: Mark posts as drafts with frontmatter
- **Date Flexibility** 📅: Use frontmatter dates or file timestamps
- **Smart File Organization** 🗃️: Git-aware file renaming to standard format
- **GitHub Pages Ready** 🚀: Generate static HTML perfect for free hosting
- **Substack Import** 📥: Import posts from Substack blogs with a single command
- **Image Support** 🖼️: Automatic image processing, optimization and thumbnails
- **Pinned Posts** 📌: Pin important posts to the top of your blog
- **Post Management** 🔧: CLI commands to publish, unpublish, and delete posts
- **SEO Friendly** 🌐: Generates proper metadata for search engines and social media

## 🤔 Motivation

Some folks such as [Simon Willison](https://simonwillison.net/) have convinced me to start blogging my thoughts. I wanted to keep things simple—just a dumb set of markdown files should be enough to create a super simple HTML blog.

Even with great tools like [Zola](https://www.getzola.org/), [Hugo](https://gohugo.io/), and [Pelican](https://getpelican.com/) available, they felt too complicated for what I needed. I wanted the minimal expression of simplicity. Hence, BlogTuner was born.

The idea is to keep your markdown files in a repo, generate HTML with BlogTuner, and deploy to a service like GitHub Pages. As simple as that.

## 📦 Installation

The recommended way to use BlogTuner is via `uvx` (by the way, if you haven't heard about `uv` you should [read about it](https://github.com/astral-sh/uv)):

```bash
uvx blogtuner build source_dir target_dir
```

If you prefer to install it:

```bash
uv pip install blogtuner
```

You can use the traditional `pip` workflow without `uv` as well.

## 🚀 Usage

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

### Post Management

BlogTuner comes with a set of commands to manage your posts:

```bash
# List all your posts
blogtuner post list

# Publish a draft post
blogtuner post publish slug-of-your-post

# Unpublish a post (mark as draft)
blogtuner post unpublish slug-of-your-post

# Delete a post
blogtuner post delete slug-of-your-post
```

### Importing Content

#### From Markdown Files

```bash
# Import a markdown file as a new post
blogtuner post import markdown /path/to/your/post.md
```

#### From Substack

```bash
# Import all posts from a Substack blog
blogtuner post import substack https://yourblog.substack.com
```

### Smart File Organization

BlogTuner automatically renames your files to follow the pattern `YYYY-MM-DD-slug.md`.

When BlogTuner normalizes your file names, it intelligently detects if the file is part of a Git repository:

- If the file is tracked in Git, it uses `git mv` to rename it, preserving your Git history
- If not, it falls back to a regular file system rename

This makes BlogTuner play nicely with your Git workflow while keeping everything organized.

### Images

BlogTuner automatically processes images for your posts:

1. Place an image with the same name as your post (e.g., `2024-04-05-my-post.jpg` for `2024-04-05-my-post.md`)
2. BlogTuner will automatically process it, create optimized WebP versions, and generate thumbnails
3. Images are referenced in your HTML and feed automatically

### Frontmatter

Posts can include TOML frontmatter at the beginning of the file (if you don't include it, it will be generated during the first run):

```markdown
+++
title = "My Awesome Post"
pubdate = "2024-04-05"
draft = false
slug = "custom-slug"  # Optional, defaults to filename
tags = ["tech", "programming"]
pinned = false  # Set to true to pin this post to the top
oneliner = "A brief description of this post"
description = "A longer description for SEO purposes"
original_href = "https://original-source.com/post"  # If republishing from elsewhere
+++

# My Awesome Post

Content goes here...
```

### Blog Configuration

Create a `blog.toml` in your source directory (it will be created on the first run if you're lazy like me):

```toml
name = "My Awesome Blog"
author = "Your Name"
base_url = "https://yourdomain.com"
base_path = "/"
lang = "en"
timezone = "UTC"
description = "A blog about interesting things"
footer_text = "Powered by <a href='https://github.com/alltuner/blogtuner'>BlogTuner</a>"
links = { "GitHub" = "https://github.com/yourusername", "Twitter" = "https://twitter.com/yourusername" }
twitter_metadata = { "site" = "@yoursite", "creator" = "@yourusername" }
```

## 🛠️ Features in Detail

### Post Processing

- **Automatic Metadata**: Extract frontmatter or use defaults
- **Date Handling**: Parse dates from frontmatter or use file timestamps
- **Drafts**: Drafts won't appear in the public index or feed
- **File Normalization**: Files renamed to YYYY-MM-DD-slug.md with Git awareness
- **Syntax Highlighting**: Code blocks are automatically highlighted
- **Format Normalization**: Markdown is normalized to ensure consistent formatting

### Site Generation

- **HTML Generation**: Clean, simple HTML for each post and index
- **Feed Generation**: RSS feed for syndication
- **CSS Bundling**: Simple, clean CSS included automatically
- **Fast Processing**: Efficient even for large numbers of posts
- **Image Processing**: Automatic optimization and thumbnail generation
- **SEO Metadata**: Proper metadata for search engines and social media

### LLM-Enhanced Features

- **Substack Import**: Uses LLM-powered conversion from HTML to Markdown
- **Content Processing**: Intelligent handling of various content types

## 🧑‍💻 Contributing

Want to contribute? Awesome! But read this first:

**I'm looking for simplicity, not complexity.**

The best contributions to BlogTuner are ones that:

- Make it even simpler to use
- Remove complexity, not add it
- Fix bugs or improve performance
- Enhance the core functionality without bloating it

If your PR adds a ton of new features or dependencies, it's probably not a good fit.

The guiding principle is: "How can we make blogging have even fewer excuses?"

Submit your PRs and let's make blogging simpler together!

## 🔄 Example Workflow

1. Write posts in Markdown with optional TOML frontmatter
2. Run BlogTuner to generate HTML and RSS feed
3. Push HTML to GitHub Pages or your hosting service
4. Repeat daily (no excuses!)

## CLI Commands Reference

```
blogtuner --help                     # Show help for all commands
blogtuner version                    # Show version
blogtuner build TARGET_DIR           # Build site to target directory
blogtuner post list                  # List all posts
blogtuner post publish SLUG          # Publish a draft post
blogtuner post unpublish SLUG        # Mark a post as draft
blogtuner post delete SLUG           # Delete a post
blogtuner post import markdown FILE  # Import a markdown file
blogtuner post import substack URL   # Import posts from Substack
```

## 👨‍💻 Author

BlogTuner is developed by [David Poblador i Garcia](https://davidpoblador.com/) as part of [All Tuner Labs](https://alltuner.com/). It's created by someone who believes blogging should be simple, fast, and without barriers.

## 📄 License

MIT
