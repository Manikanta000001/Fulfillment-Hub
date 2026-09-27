from pathlib import Path
import shutil

from sqlalchemy import create_engine


BASE_DIR = Path(__file__).resolve().parent.parent

SOURCE_DATABASE_PATH = BASE_DIR / "database" / "fulfillment.db"

# Streamlit Cloud needs a writable runtime location.
RUNTIME_DATABASE_PATH = Path("/tmp/fulfillment_hub.db")


if not RUNTIME_DATABASE_PATH.exists():
    shutil.copy2(
        SOURCE_DATABASE_PATH,
        RUNTIME_DATABASE_PATH
    )


DATABASE_URL = f"sqlite:///{RUNTIME_DATABASE_PATH}"


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)