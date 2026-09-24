"""
Load and validate HC-245 (required) and optional HC-233.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import config


class SchemaAssumptionError(RuntimeError):
    pass


def _read_stata(path: Path) -> pd.DataFrame:
    df = pd.read_stata(path, convert_categoricals=False)
    df.columns = [c.upper() for c in df.columns]
    return df


def load_longitudinal(path: Path) -> pd.DataFrame:
    df = _read_stata(path)
    validate_longitudinal_schema(df)
    return df


def load_consolidated_optional(path: Path) -> pd.DataFrame:
    df = _read_stata(path)
    validate_consolidated_schema(df)
    return df


def validate_longitudinal_schema(df: pd.DataFrame) -> None:
    missing = []
    if config.PERSON_ID not in df.columns:
        missing.append(config.PERSON_ID)
    for label, var in config.ED_VISIT_VARS.items():
        if var not in df.columns:
            missing.append(f"{var} ({label})")
    for var in config.SURVEY_DESIGN_VARS:
        if var not in df.columns:
            missing.append(var)
    if config.SDOH_ELIG not in df.columns:
        missing.append(
            f"{config.SDOH_ELIG} (required for SDOH cohort filter; "
            "expected on HC-245 Round-5 SDOH block)"
        )
    sdoh_missing = [n for n in config.sdoh_predictor_names() if n not in df.columns]
    # Require eligibility + at least one primary SDOH predictor present.
    if sdoh_missing and len(sdoh_missing) == len(config.sdoh_predictor_names()):
        missing.append(
            "primary SDOH predictor block (no SD*5 candidates present on file)"
        )

    if missing:
        raise SchemaAssumptionError(
            "HC-245 file is missing required variables: "
            f"{missing}. Refusing to guess or silently drop the cohort/SDOH rule."
        )

    if df[config.PERSON_ID].isna().any():
        raise SchemaAssumptionError(
            f"{config.PERSON_ID} contains missing values; cannot uniquely identify persons."
        )

    for var in config.ED_VISIT_VARS.values():
        col = df[var]
        non_numeric = pd.to_numeric(col, errors="coerce").isna() & col.notna()
        if non_numeric.any():
            raise SchemaAssumptionError(
                f"{var} contains non-numeric values that failed to coerce; "
                "expected a visit count."
            )


def validate_consolidated_schema(df: pd.DataFrame) -> None:
    missing = []
    if config.PERSON_ID not in df.columns:
        missing.append(config.PERSON_ID)
    if "SDOHELIG" not in df.columns:
        missing.append("SDOHELIG")
    if missing:
        raise SchemaAssumptionError(
            "HC-233 file is missing required linkage/SDOH variables: "
            f"{missing}. Refusing to proceed with a broken optional join."
        )
    if df[config.PERSON_ID].isna().any():
        raise SchemaAssumptionError(
            f"HC-233 {config.PERSON_ID} contains missing values."
        )
