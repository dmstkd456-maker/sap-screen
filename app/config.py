import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR
DATA_DIR = ROOT_DIR / "data"

# Load .env file BEFORE reading environment variables
load_dotenv(ROOT_DIR / ".env")


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


# Shared dataset path (single CSV)
SHARED_TOTAL_CSV = _path_from_env("SAP_TOTAL_DATA_PATH", DATA_DIR / "total_data.csv")

# Screen dataset paths (default to shared file for both recent/legacy slots)
SCREEN_DIR = _path_from_env("SAP_SCREEN_DIR", ROOT_DIR / "sap-screen")
SCREEN_RECENT_CSV = _path_from_env("SAP_SCREEN_RECENT_PATH", SHARED_TOTAL_CSV)
SCREEN_LEGACY_CSV = _path_from_env("SAP_SCREEN_LEGACY_PATH", SHARED_TOTAL_CSV)

# Dashboard dataset path (shared)
DASHBOARD_TOTAL_CSV = _path_from_env("SAP_DASHBOARD_TOTAL_DATA", SHARED_TOTAL_CSV)
