import json
from typing import Optional

import llm  # type: ignore
from pydantic import BaseModel


model = llm.get_model("gpt-4o-mini")


class HtmlToMarkdownLLM(BaseModel):
    html: str
    additional_info: Optional[str] = None
    title: Optional[str] = None

    @property
    def prompt(self) -> str:
        # Generate a prompt for the LLM
        return f"""
Given the following HTML code convert the HTML to markdown format.
The resulting markdown should be suitable for being the content of a blog post, which
means you will identify headings, sections, etc.

For aiding your duty, I might provide you with some additional information about the content of the HTML
and the original title of the content (if known).

You should ignore HTML that is not related to the content of the post (such as ads, or subscription forms, etc).

Make sure you transfer the links properly.

Also, ignore images.

Data:

{self.model_dump_json()}
"""


class MarkdDownContent(BaseModel):
    markdown: str


def get_markdown_from_substack(html: str, title: Optional[str] = None) -> str:
    info = HtmlToMarkdownLLM(
        html=html, additional_info="This is a Substack post", title=title
    )
    prompt = info.prompt
    response = model.prompt(prompt, schema=MarkdDownContent)
    markdown_content = json.loads(response.text())["markdown"]
    return markdown_content
