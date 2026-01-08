from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional
import csv
from models import ExtractedInfo

DATA_PATH = Path("data") / "submissions.csv"

@lru_cache(maxsize=1)
def _load_rows() -> list:
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def find_submission(info: ExtractedInfo) -> Optional[Dict[str, str]]:
    rows = _load_rows()
    if not rows:
        return None

    # Try exact match by submission number
    if info.submission_number:
        for row in rows:
            if row.get("submission_number", "").strip() == info.submission_number.strip():
                return row

    # Try exact match by normalized mobile number
    mobile = info.normalized_mobile()
    if mobile:
        for row in rows:
            row_mobile = row.get("mobile_number", "")
            row_mobile_digits = ''.join(ch for ch in row_mobile if ch.isdigit())
            if row_mobile_digits == mobile:
                return row

    # Optionally, try case-insensitive name contains match if provided and others failed
    if info.name:
        name_lower = info.name.strip().lower()
        for row in rows:
            if name_lower in row.get("name", "").strip().lower():
                return row

    return None


