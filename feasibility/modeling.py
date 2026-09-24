"""
Baselines and full logistic model.

Structural implementation matching the companion design. Real-data
fitting happens only when run.py is invoked with user-supplied files.
Unit tests may call these helpers on clearly labeled synthetic frames.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from . import config

THRESHOLD_NOTE = (
    "Threshold-dependent exploratory metrics at decision_threshold=0.5. "
    "Not an optimized operating point and not a clinical cutoff."
)


@dataclass
class EvalResult:
    model_name: str
    n_test: int
    prevalence: float
    roc_auc: float | None
    pr_auc: float | None
    brier_score: float | None
    accuracy: float
    sensitivity: float
    specificity: float
    precision: float
    recall: float
    decision_threshold: float
    threshold_metrics_note: str
    confusion: dict = field(default_factory=dict)


def split_holdout(X: pd.DataFrame, y: pd.Series):
    return train_test_split(
        X,
        y,
        test_size=config.HOLDOUT_FRACTION,
        random_state=config.RANDOM_SEED,
        stratify=y,
    )


def _classifier() -> LogisticRegression:
    return LogisticRegression(
        max_iter=2000, C=1.0, random_state=config.RANDOM_SEED
    )


def evaluate_binary(
    model_name: str,
    y_true: pd.Series,
    y_prob: np.ndarray,
    threshold: float = 0.5,
) -> EvalResult:
    y_true_arr = np.asarray(y_true).astype(int)
    y_hat = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true_arr, y_hat, labels=[0, 1]).ravel()
    prevalence = float(y_true_arr.mean()) if len(y_true_arr) else 0.0
    roc = roc_auc_score(y_true_arr, y_prob) if y_true_arr.min() != y_true_arr.max() else None
    pr = (
        average_precision_score(y_true_arr, y_prob)
        if y_true_arr.min() != y_true_arr.max()
        else None
    )
    brier = float(brier_score_loss(y_true_arr, y_prob)) if len(y_true_arr) else None
    return EvalResult(
        model_name=model_name,
        n_test=int(len(y_true_arr)),
        prevalence=prevalence,
        roc_auc=roc,
        pr_auc=pr,
        brier_score=brier,
        accuracy=float((y_hat == y_true_arr).mean()) if len(y_true_arr) else 0.0,
        sensitivity=float(tp / (tp + fn)) if (tp + fn) else 0.0,
        specificity=float(tn / (tn + fp)) if (tn + fp) else 0.0,
        precision=float(precision_score(y_true_arr, y_hat, zero_division=0)),
        recall=float(recall_score(y_true_arr, y_hat, zero_division=0)),
        decision_threshold=threshold,
        threshold_metrics_note=THRESHOLD_NOTE,
        confusion={"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    )


def baseline_prevalence(y_train: pd.Series, y_test: pd.Series) -> EvalResult:
    p = float(y_train.mean())
    y_prob = np.full(len(y_test), p)
    return evaluate_binary("baseline_1_prevalence", y_test, y_prob)


def baseline_prior_year_only(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    prior_col: str,
) -> EvalResult:
    pipe = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("clf", _classifier()),
        ]
    )
    pipe.fit(X_train[[prior_col]], y_train)
    y_prob = pipe.predict_proba(X_test[[prior_col]])[:, 1]
    return evaluate_binary("baseline_2_prior_year_ed_only", y_test, y_prob)


def baseline_three_year_history(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    hist_cols: list[str],
) -> EvalResult:
    pipe = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("clf", _classifier()),
        ]
    )
    pipe.fit(X_train[hist_cols], y_train)
    y_prob = pipe.predict_proba(X_test[hist_cols])[:, 1]
    return evaluate_binary("baseline_3_three_year_ed_history", y_test, y_prob)


def _preprocess(numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    transformers = []
    if numeric_cols:
        transformers.append(
            (
                "num",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                numeric_cols,
            )
        )
    if categorical_cols:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        (
                            "onehot",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                categorical_cols,
            )
        )
    return ColumnTransformer(transformers)


def full_logistic_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    numeric_cols: list[str],
    categorical_cols: list[str],
    model_name: str = "full_logistic",
) -> tuple[EvalResult, Pipeline, np.ndarray]:
    pipe = Pipeline(
        [
            ("prep", _preprocess(numeric_cols, categorical_cols)),
            ("clf", _classifier()),
        ]
    )
    pipe.fit(X_train, y_train)
    y_prob = pipe.predict_proba(X_test)[:, 1]
    return evaluate_binary(model_name, y_test, y_prob), pipe, y_prob


def write_calibration_outputs(
    y_true: pd.Series,
    y_prob: np.ndarray,
    csv_path: Path,
    png_path: Path,
    n_bins: int = 10,
) -> None:
    fraction_pos, mean_pred = calibration_curve(
        y_true, y_prob, n_bins=n_bins, strategy="quantile"
    )
    pd.DataFrame(
        {"mean_predicted_probability": mean_pred, "fraction_positive": fraction_pos}
    ).to_csv(csv_path, index=False)
    try:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(5, 5))
        ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Ideal")
        ax.plot(mean_pred, fraction_pos, marker="o", label="Model")
        ax.set_xlabel("Mean predicted probability")
        ax.set_ylabel("Fraction positive")
        ax.set_title("Calibration (holdout)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(png_path, dpi=120)
        plt.close(fig)
    except Exception:
        # Calibration CSV is the required artifact; figure is best-effort.
        pass
