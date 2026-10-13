"""Put this repo's src/ folder on sys.path so job files can import settings, columns, etc."""

import sys
from pathlib import Path


def add_src_to_path() -> None:
    src = Path(__file__).resolve().parent
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
