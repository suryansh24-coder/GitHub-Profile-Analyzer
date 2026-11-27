import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("APP_ROOT", str(ROOT))

from app.main import app  # noqa: E402

__all__ = ["app"]
