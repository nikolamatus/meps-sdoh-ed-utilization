"""
Panel 24 HC-245 <-> optional HC-233 linkage checks.

Primary SDOH path does not require a join (SD*5 already on HC-245).
When HC-233 is supplied, report DUPERSID match rates and fail closed
on missing/duplicate keys.
"""
from __future__ import annotations

import pandas as pd

from . import config


class LinkageError(RuntimeError):
    pass


def assert_unique_key(df: pd.DataFrame, key: str, label: str) -> None:
    if key not in df.columns:
        raise LinkageError(f"{label}: linkage key {key} is missing.")
    if df[key].isna().any():
        raise LinkageError(f"{label}: linkage key {key} has missing values.")
    n_dup = int(df[key].duplicated().sum())
    if n_dup:
        raise LinkageError(
            f"{label}: {n_dup} duplicate {key} values; cannot join persons cleanly."
        )


def panel24_subset(consolidated: pd.DataFrame) -> pd.DataFrame:
    if config.PANEL in consolidated.columns:
        panel = pd.to_numeric(consolidated[config.PANEL], errors="coerce")
        return consolidated.loc[panel == config.PANEL_24].copy()
    # Fallback: Panel 24 DUPERSID begins with "24" in post-2017 MEPS IDs.
    ids = consolidated[config.PERSON_ID].astype(str)
    mask = ids.str.startswith("24")
    if not mask.any():
        raise LinkageError(
            "HC-233: cannot identify Panel 24 rows (PANEL missing and "
            "DUPERSID does not start with '24')."
        )
    return consolidated.loc[mask].copy()


def join_report(longitudinal: pd.DataFrame, consolidated: pd.DataFrame) -> dict:
    """
    Inner/left join diagnostics for optional HC-233 validation.

    Raises LinkageError if keys are unusable.
    """
    assert_unique_key(longitudinal, config.PERSON_ID, "HC-245")
    assert_unique_key(consolidated, config.PERSON_ID, "HC-233")
    p24 = panel24_subset(consolidated)
    assert_unique_key(p24, config.PERSON_ID, "HC-233 Panel 24 subset")

    left_ids = set(longitudinal[config.PERSON_ID].astype(str))
    right_ids = set(p24[config.PERSON_ID].astype(str))
    both = left_ids & right_ids
    only_left = left_ids - right_ids
    only_right = right_ids - left_ids

    merged = longitudinal.merge(
        p24[[config.PERSON_ID, "SDOHELIG"]].rename(
            columns={"SDOHELIG": "SDOHELIG_HC233"}
        ),
        on=config.PERSON_ID,
        how="left",
        validate="one_to_one",
    )

    elig_agree = None
    if config.SDOH_ELIG in merged.columns:
        a = pd.to_numeric(merged[config.SDOH_ELIG], errors="coerce")
        b = pd.to_numeric(merged["SDOHELIG_HC233"], errors="coerce")
        comparable = a.notna() & b.notna()
        if comparable.any():
            elig_agree = float((a[comparable] == b[comparable]).mean())

    return {
        "n_hc245": len(left_ids),
        "n_hc233_panel24": len(right_ids),
        "n_matched_dupersid": len(both),
        "n_hc245_only": len(only_left),
        "n_hc233_panel24_only": len(only_right),
        "match_rate_of_hc245": len(both) / len(left_ids) if left_ids else None,
        "sdoh_elig_agreement_rate": elig_agree,
        "join_key": config.PERSON_ID,
    }


def require_sdoh_on_longitudinal(df: pd.DataFrame) -> dict:
    """HC-245-only path: confirm SDOH eligibility column exists."""
    if config.SDOH_ELIG not in df.columns:
        raise LinkageError(
            f"HC-245 is missing {config.SDOH_ELIG}; cannot apply the SDOH cohort filter."
        )
    present = [n for n in config.sdoh_predictor_names() if n in df.columns]
    if not present:
        raise LinkageError(
            "HC-245 has no primary SDOH predictor columns (SD*5). "
            "Refusing to invent names or proceed without SDOH features."
        )
    return {
        "path": "hc245_embedded_sdoh",
        "sdoh_elig_var": config.SDOH_ELIG,
        "n_sdoh_predictors_present": len(present),
        "sdoh_predictors_present": present,
    }
