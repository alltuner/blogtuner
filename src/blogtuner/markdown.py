import mdformat
import mistune
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_style_by_name


css_styles = (
    HtmlFormatter().get_style_defs(".highlight")
    + """
td.linenos {
    width: 20px;
    text-align: right;
}
"""
)


class HighlightRenderer(mistune.HTMLRenderer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, escape=False)

    def block_code(self, code, info=None):
        if not info:
            return f"\n<pre>{mistune.escape(code)}</pre>\n"
        lexer = get_lexer_by_name(info, stripall=True)
        formatter = HtmlFormatter(
            linenos=True, cssclass="highlight", style=get_style_by_name("lightbulb")
        )
        return highlight(code, lexer, formatter)


renderer = HighlightRenderer()
to_html = mistune.create_markdown(
    renderer=renderer,
    escape=False,
    plugins=["strikethrough", "footnotes", "table", "speedup"],
)


format_markdown = mdformat.text
