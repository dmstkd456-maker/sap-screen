import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR
DATA_DIR = ROOT_DIR / "data"

# Load .env file if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    pass


def _path_from_env(key: str, default: Path) -> Path:
    """Resolve a filesystem path from env or fallback to default."""
    value = os.getenv(key)
    if not value:
        return default

    path = Path(value)
    # If path is relative, resolve it relative to ROOT_DIR
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


# Shared dataset path (SQLite DB)
SHARED_TOTAL_CSV = _path_from_env("SAP_TOTAL_DATA_PATH", DATA_DIR / "sap_data_4.db")

# Screen dataset paths (default to shared file for both recent/legacy slots)
SCREEN_DIR = _path_from_env("SAP_SCREEN_DIR", ROOT_DIR / "sap-screen")
SCREEN_RECENT_CSV = _path_from_env("SAP_SCREEN_RECENT_PATH", SHARED_TOTAL_CSV)
SCREEN_LEGACY_CSV = _path_from_env("SAP_SCREEN_LEGACY_PATH", SHARED_TOTAL_CSV)

# Dashboard dataset path (shared)
DASHBOARD_TOTAL_CSV = _path_from_env("SAP_DASHBOARD_TOTAL_DATA", SHARED_TOTAL_CSV)
