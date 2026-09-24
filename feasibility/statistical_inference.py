"""
Nadeau-Bengio corrected t-tests and Holm-Bonferroni within Family B.

Reads saved fold-level CSVs; does not refit models.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from . import config

N_REPEATS = config.CV_N_REPEATS
N_SPLITS = config.CV_N_SPLITS
N_ESTIMATES = N_REPEATS * N_SPLITS
ALPHA = 0.05
DF = N_ESTIMATES - 1

NADEAU_BENGIO_FORMULA = (
    "Nadeau & Bengio (2003) corrected resampled t-test: "
    "Var_NB = (1/n + n_test/n_train) * s^2, where s^2 is the unbiased "
    "sample variance of the n paired fold-level differences, n = r*k = 25, "
    "k = 5 folds, r = 5 repeats, and n_test/n_train is the mean validation/"
    "training size ratio within each split. t = mean / sqrt(Var_NB) with "
    "df = n-1 = 24. Two-sided p-value from Student's t."
)


class InferenceInputError(ValueError):
    pass


@dataclass(frozen=True)
class NBResult:
    n: int
    mean: float
    sample_variance: float
    test_train_ratio: float
    corrected_variance: float
    corrected_se: float
    t_statistic: float
    df: int
    p_value: float


def nadeau_bengio_ttest(deltas: np.ndarray, test_train_ratio: float) -> NBResult:
    d = np.asarray(deltas, dtype=float)
    if d.size < 2:
        raise InferenceInputError("Need at least two paired differences.")
    if test_train_ratio <= 0:
        raise InferenceInputError("test/train ratio must be positive.")
    n = int(d.size)
    mean = float(d.mean())
    s2 = float(d.var(ddof=1))
    var_nb = (1.0 / n + test_train_ratio) * s2
    se = float(np.sqrt(var_nb))
    t_stat = mean / se if se > 0 else float("inf")
    df = n - 1
    p = float(2.0 * stats.t.sf(abs(t_stat), df))
    return NBResult(
        n=n,
        mean=mean,
        sample_variance=s2,
        test_train_ratio=float(test_train_ratio),
        corrected_variance=float(var_nb),
        corrected_se=se,
        t_statistic=float(t_stat),
        df=df,
        p_value=p,
    )


def holm_adjust(p_values: list[float], alpha: float = ALPHA) -> list[float]:
    p = np.asarray(p_values, dtype=float)
    if np.any(~np.isfinite(p)) or np.any((p < 0) | (p > 1)):
        raise InferenceInputError("Holm adjustment requires finite p-values in [0, 1].")
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m, dtype=float)
    running = 0.0
    for rank, idx in enumerate(order):
        candidate = min(1.0, (m - rank) * float(p[idx]))
        running = max(running, candidate)
        adj[idx] = running
    return adj.tolist()


def mean_test_train_ratio(fold_df: pd.DataFrame) -> float:
    if "n_cv_val" not in fold_df.columns or "n_cv_train" not in fold_df.columns:
        # 5-fold default
        return 1.0 / (N_SPLITS - 1)
    ratios = fold_df["n_cv_val"] / fold_df["n_cv_train"]
    return float(ratios.mean())


def run_inference(primary_cv: pd.DataFrame, family_b_cv: pd.DataFrame) -> pd.DataFrame:
    ratio = mean_test_train_ratio(primary_cv)
    rows = []

    # Continuity / Stage-3 requested contrasts + A1
    primary_contrasts = [
        ("C_five_vs_ed", "continuity", "Five-block − ED-history", "delta_roc_five_minus_ed", "delta_pr_five_minus_ed", "delta_brier_five_minus_ed", False),
        ("C_six_vs_five", "continuity", "Six-block − Five-block (SDOH marginal)", "delta_roc_six_minus_five", "delta_pr_six_minus_five", "delta_brier_six_minus_five", False),
        ("A1", "A", "Six-block full − ED-history", "delta_roc_six_minus_ed", "delta_pr_six_minus_ed", "delta_brier_six_minus_ed", False),
    ]
    for cid, family, label, roc_col, pr_col, brier_col, _ in primary_contrasts:
        for metric, col in (("roc_auc", roc_col), ("pr_auc", pr_col), ("brier", brier_col)):
            nb = nadeau_bengio_ttest(primary_cv[col].to_numpy(dtype=float), ratio)
            rows.append(
                {
                    "contrast_id": cid,
                    "family": family,
                    "contrast": label,
                    "metric": metric,
                    "mean_delta": nb.mean,
                    "corrected_se": nb.corrected_se,
                    "t_statistic": nb.t_statistic,
                    "df": nb.df,
                    "raw_p_value": nb.p_value,
                    "holm_adjusted_p_value": np.nan,
                    "test_train_ratio": nb.test_train_ratio,
                    "n_folds": nb.n,
                    "multiplicity": "none",
                }
            )

    # Family B: B1-B6, Holm within family per metric separately? Companion did Holm
    # across the family of contrasts for each metric. Looking at companion code...
    # They apply Holm across Family B contrasts for each metric column separately.
    family_b_defs = [
        ("B1", "No-age − Full", "B1_delta_roc_minus_full", "B1_delta_pr_minus_full", "B1_delta_brier_minus_full"),
        ("B2", "No-demographics − Full", "B2_delta_roc_minus_full", "B2_delta_pr_minus_full", "B2_delta_brier_minus_full"),
        ("B3", "No-health − Full", "B3_delta_roc_minus_full", "B3_delta_pr_minus_full", "B3_delta_brier_minus_full"),
        ("B4", "No-access − Full", "B4_delta_roc_minus_full", "B4_delta_pr_minus_full", "B4_delta_brier_minus_full"),
        ("B5", "No-SES − Full", "B5_delta_roc_minus_full", "B5_delta_pr_minus_full", "B5_delta_brier_minus_full"),
        ("B6", "No-SDOH − Full", "B6_delta_roc_minus_full", "B6_delta_pr_minus_full", "B6_delta_brier_minus_full"),
    ]
    ratio_b = mean_test_train_ratio(family_b_cv)
    b_rows_by_metric: dict[str, list[dict]] = {"roc_auc": [], "pr_auc": [], "brier": []}
    for cid, label, roc_col, pr_col, brier_col in family_b_defs:
        for metric, col in (("roc_auc", roc_col), ("pr_auc", pr_col), ("brier", brier_col)):
            nb = nadeau_bengio_ttest(family_b_cv[col].to_numpy(dtype=float), ratio_b)
            rec = {
                "contrast_id": cid,
                "family": "B",
                "contrast": label,
                "metric": metric,
                "mean_delta": nb.mean,
                "corrected_se": nb.corrected_se,
                "t_statistic": nb.t_statistic,
                "df": nb.df,
                "raw_p_value": nb.p_value,
                "holm_adjusted_p_value": np.nan,
                "test_train_ratio": nb.test_train_ratio,
                "n_folds": nb.n,
                "multiplicity": "holm_within_family_B",
            }
            b_rows_by_metric[metric].append(rec)

    for metric, recs in b_rows_by_metric.items():
        adj = holm_adjust([r["raw_p_value"] for r in recs], ALPHA)
        for r, p_adj in zip(recs, adj):
            r["holm_adjusted_p_value"] = p_adj
            rows.append(r)

    return pd.DataFrame(rows)


def write_inference_summary(path, result: pd.DataFrame) -> None:
    lines = [
        "# Statistical inference (Nadeau-Bengio + Holm)",
        "",
        NADEAU_BENGIO_FORMULA,
        "",
        "## Contrasts",
        "",
        "| ID | Family | Contrast | Metric | Mean Δ | Corrected SE | t | df | raw p | Holm p |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in result.iterrows():
        holm = (
            f"{r['holm_adjusted_p_value']:.4g}"
            if pd.notna(r["holm_adjusted_p_value"])
            else "—"
        )
        lines.append(
            f"| {r['contrast_id']} | {r['family']} | {r['contrast']} | {r['metric']} | "
            f"{r['mean_delta']:+.4f} | {r['corrected_se']:.4f} | {r['t_statistic']:+.3f} | "
            f"{int(r['df'])} | {r['raw_p_value']:.4g} | {holm} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Family A (A1): Nadeau-Bengio only; no multiplicity adjustment.",
            "- Continuity contrasts (five vs ED; six vs five): reported for the",
            "  Stage-3 continuity request; not additional Family A hypotheses.",
            "- Family B (B1-B6): Holm-Bonferroni within family, per metric.",
            "- B6 (No-SDOH − Full) equals -(Six-block − Five-block) on the same folds.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
