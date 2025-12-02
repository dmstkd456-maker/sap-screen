from pathlib import Path

import pandas as pd

from app import config

_df = None
DATA_PATH = config.DASHBOARD_TOTAL_CSV


def load_data() -> pd.DataFrame:
    """Load data file (CSV or SQLite DB) with basic normalization and simple in-memory cache."""
    global _df
    if _df is None:
        try:
            print(f"[data_loader] Loading data from: {DATA_PATH}")
            print(f"[data_loader] File exists: {DATA_PATH.exists()}")
            print(f"[data_loader] File suffix: {DATA_PATH.suffix}")

            # Check if file is SQLite database
            if DATA_PATH.suffix.lower() == '.db':
                print(f"[data_loader] Reading SQLite database...")
                import sqlite3
                conn = sqlite3.connect(str(DATA_PATH))
                df = pd.read_sql_query(
                    "SELECT * FROM sap_reports",
                    conn,
                    dtype={"Equipment": str}
                )
                conn.close()
                print(f"[data_loader] Loaded {len(df)} rows from database")
            else:
                print(f"[data_loader] Reading CSV file...")
                # Read CSV file
                df = pd.read_csv(
                    DATA_PATH,
                    dtype={"Equipment": str},
                    encoding="utf-8-sig",
                    low_memory=False,
                )
                print(f"[data_loader] Loaded {len(df)} rows from CSV")

            df["Order Short Text"] = df["Order Short Text"].astype(str)
            df["Finish Execution"] = df["Finish Execution"].astype(str)
            df["Equipment"] = (
                df["Equipment"].fillna("").astype(str).str.replace(r"\\.0$", "", regex=True).str.strip()
            )
            _df = df
            print(f"[data_loader] Data processing complete, {len(_df)} rows ready")
        except FileNotFoundError as e:
            print(f"[data_loader] ERROR: File not found - {e}")
            _df = pd.DataFrame()
        except Exception as e:
            print(f"[data_loader] ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            _df = pd.DataFrame()
    else:
        print(f"[data_loader] Using cached data: {len(_df)} rows")
    return _df
