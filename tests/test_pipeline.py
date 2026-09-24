"""
Tests against clearly labeled SYNTHETIC frames only.

These are not MEPS results. No real HC-245 / HC-233 microdata are
required or accessed.
"""
from __future__ import annotations

import pandas as pd
import pytest

from feasibility import config, features, linkage, longitudinal, report
from feasibility.config import FeatureMetadataError, FeatureSpec, validate_feature_metadata


def _survey_cols(n, yearind=1, all9=1):
    return {
        config.YEARIND: [yearind] * n,
        config.ALL9RDS: [all9] * n,
        config.LONGWT: [1.0] * n,
        config.VARSTR: [1] * n,
        config.VARPSU: [1] * n,
    }


def _synthetic_cohort_df():
    """Synthetic person-level frame for unit tests (NOT MEPS microdata)."""
    n = 6
    data = {
        config.PERSON_ID: [f"24P{i}" for i in range(n)],
        "ERTOTY1": [0, 1, -1, 2, 0, 1],
        "ERTOTY2": [0, 0, 3, 2, 1, 0],
        "ERTOTY3": [1, 0, 2, -7, 0, 1],
        "ERTOTY4": [0, 2, 1, 0, 1, 0],
        "SEX": [1, 2, 1, 2, 1, 2],
        "RACETHX": [1, 2, 3, 1, 2, 1],
        "AGEY3X": [40, 55, 12, 70, 33, 48],
        "REGIONY3": [1, 2, 3, 4, 1, 2],
        "MARRY6X": [1, 2, 1, 2, 1, 2],
        "RTHLTH6": [1, 3, 2, 4, 2, 1],
        "MNHLTH6": [1, 2, 3, 2, 1, 2],
        "INSCOVY3": [1, 2, 3, 1, 2, 1],
        "HAVEUS6": [1, 1, 2, 1, 1, 2],
        "POVCATY3": [1, 3, 4, 2, 1, 3],
        "TTLPY3X": [20000, 40000, -1, 80000, 25000, 50000],
        "EMPST6": [1, 2, -1, 1, 1, 2],
        config.SDOH_ELIG: [1, 1, 0, 1, 2, 1],
        "SDAFRDHOME5": [3, 4, -1, 2, -1, 5],
        "SDWRRYFD5": [1, 2, -1, 1, -1, 2],
        "SDNOTRANS5": [1, 1, -1, 2, -1, 1],
        "SDPAYBASICS5": [2, 3, -1, 1, -1, 4],
        "SDFAMILY5": [1, 2, -1, 1, -1, 2],
        "SDSFCRIME5": [2, 3, -1, 1, -1, 2],
        "SDHMDEPR5": [1, 2, -1, 1, -1, 2],
        **_survey_cols(n),
    }
    return pd.DataFrame(data)


def test_config_sdoh_block_all_pre_cutoff():
    for spec in config.SDOH_FEATURES:
        assert spec.documentation_status == "confirmed"
        assert spec.availability_year == 2021
        assert spec.allowed_by_cutoff
        assert spec.family == "sdoh"


def test_sdoh_elig_cannot_enter_x():
    with pytest.raises(features.LeakageError):
        features.build_feature_matrix(_synthetic_cohort_df(), [config.SDOH_ELIG])


def test_cohort_requires_sdoh_elig_has_data():
    df = _synthetic_cohort_df()
    usable = longitudinal.usable_prediction_population(df)
    # Rows with valid ED + YEARIND + SDOHELIG5==1: indices 0,1,5
    # index 3 has ERTOTY3=-7 invalid; index 2 not eligible; index 4 elig=2
    assert set(usable[config.PERSON_ID]) == {"24P0", "24P1", "24P5"}


def test_companion_cohort_larger_than_sdoh_cohort():
    df = _synthetic_cohort_df()
    companion = longitudinal.companion_prediction_population(df)
    usable = longitudinal.usable_prediction_population(df)
    assert len(companion) >= len(usable)
    assert "24P0" in set(companion[config.PERSON_ID])


def test_duplicate_persons_fail():
    df = _synthetic_cohort_df()
    df.loc[1, config.PERSON_ID] = "24P0"
    with pytest.raises(longitudinal.CohortDefinitionError):
        longitudinal.assert_unique_persons(df)


def test_leakage_rejects_ertoty4_and_y4_aliases():
    df = _synthetic_cohort_df()
    with pytest.raises(features.LeakageError):
        features.build_feature_matrix(df, ["ERTOTY1", "ERTOTY4"])
    df = df.copy()
    df["AGEY4X"] = 50
    with pytest.raises(features.LeakageError):
        features.build_feature_matrix(df, ["AGEY3X", "AGEY4X"])


def test_round_8_9_cannot_enter_x():
    assert features.looks_post_cutoff("RTHLTH8")
    assert features.looks_post_cutoff("EMPST9")
    assert not features.looks_post_cutoff("RTHLTH6")
    assert not features.looks_post_cutoff("SDAFRDHOME5")


def test_unknown_column_fails_closed():
    with pytest.raises(features.LeakageError, match="no FeatureSpec"):
        features.build_feature_matrix(_synthetic_cohort_df(), ["NOT_A_REAL_VARIABLE"])


def test_post_cutoff_cannot_be_marked_allowed():
    illegal = FeatureSpec(
        name="AGEY4X",
        family="demographics",
        description="should fail",
        availability_year=2022,
        time_invariant=False,
        allowed_by_cutoff=True,
        treatment="numeric",
        documentation_status="confirmed",
    )
    with pytest.raises(FeatureMetadataError):
        validate_feature_metadata(illegal)


def test_negative_sentinels_become_missing():
    series = pd.Series([0, 1, -1, -7, -8, -9, -15, 3])
    recoded = features.recode_sentinels(series)
    assert recoded.tolist()[:2] == [0.0, 1.0]
    assert recoded.iloc[2:7].isna().all()
    assert recoded.iloc[7] == 3.0


def test_feature_audit_marks_present_sdoh_usable():
    df = _synthetic_cohort_df()
    audit = features.build_feature_audit(df)
    row = audit.loc[audit["feature"] == "SDAFRDHOME5"].iloc[0]
    assert row["present_in_file"]
    assert row["usable"]
    assert row["allowed_by_cutoff"]


def test_linkage_requires_unique_dupersid():
    left = _synthetic_cohort_df()
    right = left.copy()
    right.loc[1, config.PERSON_ID] = "24P0"
    with pytest.raises(linkage.LinkageError, match="duplicate"):
        linkage.assert_unique_key(right, config.PERSON_ID, "synthetic-right")


def test_linkage_join_report_on_synthetic_frames():
    """Synthetic HC-245 / HC-233-like frames — not real MEPS output."""
    hc245 = _synthetic_cohort_df()
    hc233 = pd.DataFrame(
        {
            config.PERSON_ID: hc245[config.PERSON_ID].tolist()
            + ["25P9"],
            config.PANEL: [24] * len(hc245) + [25],
            "SDOHELIG": [1, 1, 0, 1, 2, 1, 1],
        }
    )
    report_dict = linkage.join_report(hc245, hc233)
    assert report_dict["n_matched_dupersid"] == len(hc245)
    assert report_dict["n_hc233_panel24_only"] == 0
    assert report_dict["join_key"] == config.PERSON_ID


def test_require_sdoh_on_longitudinal_fails_without_block():
    df = _synthetic_cohort_df().drop(
        columns=[c for c in _synthetic_cohort_df().columns if c.startswith("SD")]
    )
    with pytest.raises(linkage.LinkageError):
        linkage.require_sdoh_on_longitudinal(df)


def test_decision_gate_red_on_tiny_n():
    color, components = report.decide_gate(
        {
            "usable_n": 50,
            "n_outcome_events": 5,
            "outcome_prevalence": 0.1,
            "families_present": {"prior_utilization", "demographics", "sdoh", "access"},
            "n_allowed_candidates": 10,
            "n_present_allowed": 10,
            "longitudinal_ok": True,
            "leakage_ok": True,
            "calibration_produced": True,
            "unique_persons": True,
            "weighted": False,
            "baseline2_roc_auc": 0.7,
            "full_roc_auc": 0.75,
            "full_pr_auc": 0.3,
            "best_ed_baseline_roc_auc": 0.7,
            "best_ed_baseline_pr_auc": 0.25,
        }
    )
    assert color == "RED"
    assert components["data_adequacy"]["status"] == "FAIL"


def test_decision_gate_requires_sdoh_family():
    color, components = report.decide_gate(
        {
            "usable_n": 2000,
            "n_outcome_events": 200,
            "outcome_prevalence": 0.1,
            "families_present": {
                "prior_utilization",
                "demographics",
                "access",
            },
            "n_allowed_candidates": 10,
            "n_present_allowed": 10,
            "longitudinal_ok": True,
            "leakage_ok": True,
            "calibration_produced": True,
            "unique_persons": True,
            "weighted": False,
            "baseline2_roc_auc": 0.7,
            "full_roc_auc": 0.78,
            "full_pr_auc": 0.35,
            "best_ed_baseline_roc_auc": 0.7,
            "best_ed_baseline_pr_auc": 0.25,
        }
    )
    assert color == "RED"
    assert any("sdoh" in r for r in components["data_adequacy"]["reasons"])
