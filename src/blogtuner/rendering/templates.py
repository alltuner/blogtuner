from jinja2 import Environment, FileSystemLoader, Template

from blogtuner.utils.paths import get_resource_path


def get_jinja_env() -> Environment:
    """Get the Jinja2 environment.

    Returns:
        Jinja2 environment object
    """
    jinja_env = Environment(
        autoescape=True,
        loader=FileSystemLoader(get_resource_path("templates")),
    )
    jinja_env.filters["date"] = lambda value, format=None: value.strftime(
        format if format else "%Y-%m-%d"
    )
    return jinja_env


def load_template(name: str) -> Template:
    """Load a template by name.

    Args:
        name: Template name without extension

    Returns:
        Jinja2 template object
    """
    jinja_env = get_jinja_env()

    return jinja_env.get_template(f"{name}.html.jinja")
