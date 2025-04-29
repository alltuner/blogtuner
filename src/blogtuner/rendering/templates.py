from babel.support import Translations
from jinja2 import Environment, FileSystemLoader, Template

from blogtuner.utils.paths import get_resource_path


def get_jinja_env(locale="en") -> Environment:
    """Get the Jinja2 environment with i18n support.

    Args:
        locale: The locale code to use (e.g., 'en', 'es', 'fr')

    Returns:
        Jinja2 environment object
    """
    # Load translations for the specified locale
    translations = Translations.load(get_resource_path("l10n"), [locale])

    jinja_env = Environment(
        autoescape=True,
        loader=FileSystemLoader(get_resource_path("templates")),
        extensions=["jinja2.ext.i18n"],  # Add i18n extension
    )

    # Install gettext functions
    jinja_env.install_gettext_translations(translations)

    jinja_env.filters["date"] = lambda value, format=None: value.strftime(
        format if format else "%Y-%m-%d"
    )

    return jinja_env


def load_template(name: str, locale: str = "en") -> Template:
    """Load a template by name with specified locale.

    Args:
        name: Template name without extension
        locale: Locale code for translations

    Returns:
        Jinja2 template object
    """
    jinja_env = get_jinja_env(locale)
    return jinja_env.get_template(f"{name}.html.jinja")
