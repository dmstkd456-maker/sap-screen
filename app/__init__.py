import os
from pathlib import Path

from flask import Flask

from app.routes.search import search_bp
from app.routes.dashboard import dashboard_bp


BASE_DIR = Path(__file__).resolve().parent.parent

# Load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


def create_app() -> Flask:
    # Point Flask to shared template/static dirs at project root
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.secret_key = "supersecretkey"  # TODO: move to environment

    app.config["ASSET_VERSION"] = os.getenv("ASSET_VERSION", "1")

    @app.context_processor
    def inject_asset_version():
        return {"asset_version": app.config["ASSET_VERSION"]}

    app.register_blueprint(search_bp)
    app.register_blueprint(dashboard_bp)

    return app
