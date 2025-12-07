import os
from pathlib import Path

from flask import Flask

from app.routes.search import search_bp
from app.routes.dashboard import dashboard_bp
from app.services import data_store as ds


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

    # Warm up in-memory datastore on startup so 첫 페이지 로딩 시 데이터 적재 지연을 줄임
    try:
        ds._get_data_store()
    except Exception as exc:
        # 초기 로딩 실패해도 앱이 뜨도록만 처리; 로깅은 콘솔로 남김
        print(f"[app] 데이터 스토어 초기 로딩 실패: {exc}")

    return app
