"""Flask application factory.

A factory function (rather than a module-level `app = Flask(...)`) lets
tests or other entry points build independent app instances with
different config — `run.py` is the only thing that calls this today, but
it's the standard Flask way to structure a multi-blueprint app.
"""

from __future__ import annotations

from flask import Flask

from .config import Config

# Missing any of these doesn't fail loudly on its own — e.g. a missing
# ACC_PROJECT_ID just becomes the Python string "None" wherever it's
# formatted into a URL, which Autodesk's API then rejects deep inside a
# request with a cryptic "must be a valid GUID" error. Checking here
# instead fails at startup, with a message that says what's actually wrong.
_REQUIRED_CONFIG_KEYS = ("APS_CLIENT_ID", "APS_CLIENT_SECRET", "ACC_PROJECT_ID")


def create_app(config_class: type[Config] = Config) -> Flask:
    """Builds and returns a fully configured Flask app.

    Args:
        config_class (type[Config], optional): Config object to load.

    Returns:
        Flask: The configured app, with every blueprint registered.

    Raises:
        RuntimeError: If a required environment variable wasn't set.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_class)

    missing = [key for key in _REQUIRED_CONFIG_KEYS if not app.config.get(key)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Copy .env.example to .env and fill in real values."
        )

    from .auth_routes import auth_bp
    from .main_routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app
