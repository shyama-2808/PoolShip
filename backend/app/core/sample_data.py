"""Reads the shared sample data file (backend/data/sample_data.json)."""
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

SAMPLE_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "sample_data.json"


@lru_cache(maxsize=1)
def load_sample_data() -> Dict[str, Any]:
    with open(SAMPLE_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)
