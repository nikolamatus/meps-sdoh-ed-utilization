"""
Longitudinal + SDOH cohort construction.
"""
from __future__ import annotations

import pandas as pd

from . import config
from .features import is_valid_observed


class CohortDefinitionError(RuntimeError):
    pass


def duplicate_person_check(df: pd.DataFrame) -> dict:
    n_rows = len(df)
    n_unique = df[config.PERSON_ID].nunique()
    return {
        "n_rows": n_rows,
        "n_unique_persons": n_unique,
        "n_duplicate_person_rows": n_rows - n_unique,
    }


def assert_unique_persons(df: pd.DataFrame) -> None:
    dup = df[config.PERSON_ID].duplicated()
    if dup.any():
        raise CohortDefinitionError(
            f"{int(dup.sum())} duplicate {config.PERSON_ID} values; "
            "cannot treat rows as unique persons."
        )


def valid_ed_all_four_years(df: pd.DataFrame) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for var in config.PREDICTOR_ED_VARS + [config.OUTCOME_ED_VAR]:
        mask &= is_valid_observed(df[var])
    return mask


def yearind_all_four_years(df: pd.DataFrame) -> pd.Series:
    yearind = pd.to_numeric(df[config.YEARIND], errors="coerce")
    return yearind == config.YEARIND_ALL_FOUR_YEARS


def sdoh_has_data(df: pd.DataFrame) -> pd.Series:
    if config.SDOH_ELIG not in df.columns:
        raise CohortDefinitionError(
            f"{config.SDOH_ELIG} is required for the SDOH-restricted cohort."
        )
    elig = pd.to_numeric(df[config.SDOH_ELIG], errors="coerce")
    return elig == config.SDOH_ELIG_HAS_DATA


def all9rds_complete(df: pd.DataFrame) -> pd.Series:
    flag = pd.to_numeric(df[config.ALL9RDS], errors="coerce")
    return flag == 1


def companion_prediction_population(df: pd.DataFrame) -> pd.DataFrame:
    """YEARIND==1 AND valid ED counts (companion rule, no SDOH filter)."""
    if config.YEARIND not in df.columns:
        raise CohortDefinitionError(
            f"{config.YEARIND} is required for the longitudinal cohort rule."
        )
    mask = yearind_all_four_years(df) & valid_ed_all_four_years(df)
    return df.loc[mask].copy()


def usable_prediction_population(df: pd.DataFrame) -> pd.DataFrame:
    """
    Primary analytic cohort for this repository:
    companion rule AND SDOHELIG5 == 1.
    """
    companion = companion_prediction_population(df)
    mask = sdoh_has_data(companion)
    return companion.loc[mask].copy()


def cohort_summary(df: pd.DataFrame, usable: pd.DataFrame) -> dict:
    companion = companion_prediction_population(df)
    n_all9 = int(all9rds_complete(df).sum()) if config.ALL9RDS in df.columns else None
    n_usable_and_all9 = (
        int(all9rds_complete(usable).sum()) if config.ALL9RDS in usable.columns else None
    )
    return {
        "cohort_rule": (
            "YEARIND==1 AND valid non-sentinel ERTOTY1–Y4 AND SDOHELIG5==1"
        ),
        "n_raw": int(len(df)),
        "n_yearind_all_four_years": int(yearind_all_four_years(df).sum()),
        "n_valid_ed_all_four_years": int(valid_ed_all_four_years(df).sum()),
        "n_sdoh_elig_has_data": int(sdoh_has_data(df).sum()),
        "n_companion_cohort": int(len(companion)),
        "n_all9rds": n_all9,
        "n_analytic_cohort": int(len(usable)),
        "n_analytic_and_all9rds": n_usable_and_all9,
        "weights_applied": False,
        "survey_weight_note": (
            "LONGWT/VARSTR/VARPSU (and SDOHWT21F if HC-233 joined) are recorded "
            "if present and are not applied. Metrics are unweighted predictive "
            "performance on the analytic sample."
        ),
    }
