"""
Training-only 5x5 repeated stratified CV for ED / five-block / six-block models,
plus leave-one-block-out Family B folds.

Holdout is reconstructed with seed 42 and scored once for confirmation only.
"""
from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold

from . import config, features, modeling

HOLDOUT_SEED = config.RANDOM_SEED
CV_N_SPLITS = config.CV_N_SPLITS
CV_N_REPEATS = config.CV_N_REPEATS
CV_RANDOM_STATE = config.CV_RANDOM_STATE

ED_COLUMNS = list(config.PREDICTOR_ED_VARS)
FIVE_BLOCK_COLUMNS = [
    "AGEY3X",
    "SEX",
    "RACETHX",
    "REGIONY3",
    "MARRY6X",
    "RTHLTH6",
    "MNHLTH6",
    "INSCOVY3",
    "HAVEUS6",
    "POVCATY3",
    "TTLPY3X",
    "EMPST6",
    *ED_COLUMNS,
]
SIX_BLOCK_COLUMNS = FIVE_BLOCK_COLUMNS + list(config.sdoh_predictor_names())

# Family B: leave-one-block-out vs six-block full
FAMILY_B_REMOVED = {
    "B1": ("age", list(config.BLOCK_DEFINITIONS["age"])),
    "B2": ("demographics", list(config.BLOCK_DEFINITIONS["demographics"])),
    "B3": ("health_status", list(config.BLOCK_DEFINITIONS["health_status"])),
    "B4": ("access", list(config.BLOCK_DEFINITIONS["access"])),
    "B5": ("socioeconomic", list(config.BLOCK_DEFINITIONS["socioeconomic"])),
    "B6": ("sdoh", list(config.BLOCK_DEFINITIONS["sdoh"])),
}


def training_portion(X: pd.DataFrame, y: pd.Series):
    return modeling.split_holdout(X, y)


def cv_splitter() -> RepeatedStratifiedKFold:
    return RepeatedStratifiedKFold(
        n_splits=CV_N_SPLITS,
        n_repeats=CV_N_REPEATS,
        random_state=CV_RANDOM_STATE,
    )


def describe_numeric(values: pd.Series) -> dict:
    s = pd.to_numeric(values, errors="coerce").dropna()
    return {
        "n": int(s.shape[0]),
        "mean": float(s.mean()),
        "std": float(s.std(ddof=1)) if len(s) > 1 else 0.0,
        "median": float(s.median()),
        "min": float(s.min()),
        "max": float(s.max()),
        "p2_5": float(s.quantile(0.025)),
        "p97_5": float(s.quantile(0.975)),
    }


def fit_on_fold(X_tr, y_tr, X_va, y_va, cols: list[str], model_name: str):
    present = [c for c in cols if c in X_tr.columns]
    features.assert_no_leakage(present)
    numeric, categorical = features.split_columns_by_treatment(present)
    result, _pipe, _prob = modeling.full_logistic_model(
        X_tr[present],
        y_tr,
        X_va[present],
        y_va,
        numeric,
        categorical,
        model_name=model_name,
    )
    return result


def _present(cols: list[str], X: pd.DataFrame) -> list[str]:
    return [c for c in cols if c in X.columns]


def run_primary_repeated_cv(X_train: pd.DataFrame, y_train: pd.Series) -> pd.DataFrame:
    """ED vs five-block vs six-block on the same 25 folds."""
    X_train = X_train.reset_index(drop=True)
    y_train = pd.Series(np.asarray(y_train), name="y")
    ed_cols = _present(ED_COLUMNS, X_train)
    five_cols = _present(FIVE_BLOCK_COLUMNS, X_train)
    six_cols = _present(SIX_BLOCK_COLUMNS, X_train)
    rows = []
    for i, (tr_idx, va_idx) in enumerate(cv_splitter().split(X_train, y_train)):
        repeat = i // CV_N_SPLITS
        fold = i % CV_N_SPLITS
        X_tr, X_va = X_train.iloc[tr_idx], X_train.iloc[va_idx]
        y_tr, y_va = y_train.iloc[tr_idx], y_train.iloc[va_idx]
        ed = fit_on_fold(X_tr, y_tr, X_va, y_va, ed_cols, "ed_history")
        five = fit_on_fold(X_tr, y_tr, X_va, y_va, five_cols, "five_block")
        six = fit_on_fold(X_tr, y_tr, X_va, y_va, six_cols, "six_block")
        rows.append(
            {
                "repeat": repeat,
                "fold": fold,
                "fold_index": i,
                "n_cv_train": int(len(y_tr)),
                "n_cv_val": int(len(y_va)),
                "val_prevalence": float(np.mean(y_va)),
                "ed_roc_auc": ed.roc_auc,
                "ed_pr_auc": ed.pr_auc,
                "ed_brier": ed.brier_score,
                "five_roc_auc": five.roc_auc,
                "five_pr_auc": five.pr_auc,
                "five_brier": five.brier_score,
                "six_roc_auc": six.roc_auc,
                "six_pr_auc": six.pr_auc,
                "six_brier": six.brier_score,
                "delta_roc_five_minus_ed": five.roc_auc - ed.roc_auc,
                "delta_pr_five_minus_ed": five.pr_auc - ed.pr_auc,
                "delta_brier_five_minus_ed": five.brier_score - ed.brier_score,
                "delta_roc_six_minus_five": six.roc_auc - five.roc_auc,
                "delta_pr_six_minus_five": six.pr_auc - five.pr_auc,
                "delta_brier_six_minus_five": six.brier_score - five.brier_score,
                "delta_roc_six_minus_ed": six.roc_auc - ed.roc_auc,
                "delta_pr_six_minus_ed": six.pr_auc - ed.pr_auc,
                "delta_brier_six_minus_ed": six.brier_score - ed.brier_score,
                # A1 aliases (pre-registration: full = six-block)
                "delta_roc_auc": six.roc_auc - ed.roc_auc,
                "delta_pr_auc": six.pr_auc - ed.pr_auc,
                "delta_brier": six.brier_score - ed.brier_score,
                "holdout_seed": HOLDOUT_SEED,
                "cv_random_state": CV_RANDOM_STATE,
                "n_splits": CV_N_SPLITS,
                "n_repeats": CV_N_REPEATS,
                "holdout_used": False,
            }
        )
    return pd.DataFrame(rows)


def run_family_b_repeated_cv(X_train: pd.DataFrame, y_train: pd.Series) -> pd.DataFrame:
    """Leave-one-block-out vs six-block full on the same fold indices."""
    X_train = X_train.reset_index(drop=True)
    y_train = pd.Series(np.asarray(y_train), name="y")
    six_cols = _present(SIX_BLOCK_COLUMNS, X_train)
    rows = []
    for i, (tr_idx, va_idx) in enumerate(cv_splitter().split(X_train, y_train)):
        repeat = i // CV_N_SPLITS
        fold = i % CV_N_SPLITS
        X_tr, X_va = X_train.iloc[tr_idx], X_train.iloc[va_idx]
        y_tr, y_va = y_train.iloc[tr_idx], y_train.iloc[va_idx]
        full = fit_on_fold(X_tr, y_tr, X_va, y_va, six_cols, "six_block")
        row = {
            "repeat": repeat,
            "fold": fold,
            "fold_index": i,
            "n_cv_train": int(len(y_tr)),
            "n_cv_val": int(len(y_va)),
            "full_roc_auc": full.roc_auc,
            "full_pr_auc": full.pr_auc,
            "full_brier": full.brier_score,
            "holdout_seed": HOLDOUT_SEED,
            "cv_random_state": CV_RANDOM_STATE,
        }
        for cid, (block_name, removed) in FAMILY_B_REMOVED.items():
            reduced = [c for c in six_cols if c not in removed]
            red = fit_on_fold(
                X_tr, y_tr, X_va, y_va, reduced, f"no_{block_name}"
            )
            row[f"{cid}_roc_auc"] = red.roc_auc
            row[f"{cid}_pr_auc"] = red.pr_auc
            row[f"{cid}_brier"] = red.brier_score
            row[f"{cid}_delta_roc_minus_full"] = red.roc_auc - full.roc_auc
            row[f"{cid}_delta_pr_minus_full"] = red.pr_auc - full.pr_auc
            row[f"{cid}_delta_brier_minus_full"] = red.brier_score - full.brier_score
            row[f"{cid}_block_removed"] = block_name
        rows.append(row)
    return pd.DataFrame(rows)


def run_holdout_confirmation(
    X_train, y_train, X_holdout, y_holdout
) -> pd.DataFrame:
    specs = [
        ("ed_history", ED_COLUMNS),
        ("five_block", FIVE_BLOCK_COLUMNS),
        ("six_block", SIX_BLOCK_COLUMNS),
    ]
    rows = []
    for name, cols in specs:
        present = _present(cols, X_train)
        result = fit_on_fold(
            X_train, y_train, X_holdout, y_holdout, present, name
        )
        rows.append(dataclasses.asdict(result))
    return pd.DataFrame(rows)
