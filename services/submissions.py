from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from models import ExtractedInfo


DATA_PATH = Path("data") / "submissions.csv"


@lru_cache(maxsize=1)
def _load_df() -> pd.DataFrame:
    if not DATA_PATH.exists():
        # Return empty dataframe with expected columns if file is missing
        return pd.DataFrame(
            columns=[
                "submission_number",
                "name",
                "mobile_number",
                "policy_type",
                "status",
                "premium",
                "created_at",
            ]
        )
    return pd.read_csv(DATA_PATH, dtype=str).fillna("")


def find_submission(info: ExtractedInfo) -> Optional[Dict[str, str]]:
    df = _load_df()
    if df.empty:
        return None

    # Try exact match by submission number
    if info.submission_number:
        match = df.loc[df["submission_number"].str.strip() == info.submission_number.strip()]
        if not match.empty:
            return match.iloc[0].to_dict()

    # Try exact match by normalized mobile number
    mobile = info.normalized_mobile()
    if mobile:
        # Normalize dataset mobile as digits only
        df_norm = df.copy()
        df_norm["__mobile_digits__"] = df_norm["mobile_number"].astype(str).str.replace(r"\D", "", regex=True)
        match = df_norm.loc[df_norm["__mobile_digits__"] == mobile]
        if not match.empty:
            return match.iloc[0].drop(labels="__mobile_digits__").to_dict()

    # Optionally, try case-insensitive name contains match if provided and others failed
    if info.name:
        name_lower = info.name.strip().lower()
        match = df.loc[df["name"].str.lower().str.contains(name_lower, na=False)]
        if not match.empty:
            return match.iloc[0].to_dict()

    return None


