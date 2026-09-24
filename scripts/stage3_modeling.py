"""
Stage 3+4: holdout, repeated CV, Family B ablation, inference, decision gate.

Runs only after Gates 1 and 2 have passed (caller responsibility).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from feasibility import (
    config,
    download,
    features,
    ingest,
    longitudinal,
    modeling,
    repeated_cv,
    report,
    statistical_inference as si,
)


def _summarize_primary(fold_df: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "ed_roc_auc",
        "ed_pr_auc",
        "ed_brier",
        "five_roc_auc",
        "five_pr_auc",
        "five_brier",
        "six_roc_auc",
        "six_pr_auc",
        "six_brier",
        "delta_roc_five_minus_ed",
        "delta_pr_five_minus_ed",
        "delta_brier_five_minus_ed",
        "delta_roc_six_minus_five",
        "delta_pr_six_minus_five",
        "delta_brier_six_minus_five",
        "delta_roc_six_minus_ed",
        "delta_pr_six_minus_ed",
        "delta_brier_six_minus_ed",
    ]
    rows = []
    for col in metrics:
        stats = repeated_cv.describe_numeric(fold_df[col])
        stats["metric"] = col
        rows.append(stats)
    return pd.DataFrame(rows)


def main() -> int:
    out = config.OUTPUTS_DIR
    out.mkdir(parents=True, exist_ok=True)
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    files = download.main()
    df = ingest.load_longitudinal(files["longitudinal"])
    longitudinal.assert_unique_persons(df)
    usable = longitudinal.usable_prediction_population(df)

    audit = features.build_feature_audit(usable)
    usable_cols = features.usable_predictor_columns(audit)
    # Restrict to pre-registered six-block set that is present
    six_cols = [c for c in repeated_cv.SIX_BLOCK_COLUMNS if c in usable_cols]
    features.assert_no_leakage(six_cols)
    X = features.build_feature_matrix(usable, six_cols)
    y = features.build_outcome(usable)["future_ed_visit"].astype(int)

    n_events = int(y.sum())
    prevalence = float(y.mean())
    print(f"Analytic N={len(usable)} events={n_events} prevalence={prevalence:.4f}")
    print(f"Predictors in X: {len(six_cols)}")

    X_train, X_holdout, y_train, y_holdout = repeated_cv.training_portion(X, y)
    print(f"Train={len(y_train)} holdout={len(y_holdout)}")

    # Holdout confirmation (first-run internal evaluation)
    holdout_df = repeated_cv.run_holdout_confirmation(
        X_train, y_train, X_holdout, y_holdout
    )
    holdout_df.to_csv(out / "model_metrics.csv", index=False)
    holdout_df.to_csv(out / "holdout_confirmation.csv", index=False)

    # Calibration for six-block on holdout
    six_present = [c for c in repeated_cv.SIX_BLOCK_COLUMNS if c in X_train.columns]
    numeric, categorical = features.split_columns_by_treatment(six_present)
    full_result, _pipe, y_prob = modeling.full_logistic_model(
        X_train[six_present],
        y_train,
        X_holdout[six_present],
        y_holdout,
        numeric,
        categorical,
        model_name="six_block",
    )
    modeling.write_calibration_outputs(
        y_holdout,
        y_prob,
        out / "calibration.csv",
        config.FIGURES_DIR / "calibration.png",
    )
    preds = X_holdout.copy()
    preds["y_true"] = y_holdout.values
    preds["y_prob"] = y_prob
    preds.to_csv(out / "predictions.csv", index=False)

    print("Running primary 5x5 repeated CV (ED / five / six)...")
    primary_cv = repeated_cv.run_primary_repeated_cv(X_train, y_train)
    primary_cv.to_csv(out / "repeated_cv_metrics.csv", index=False)
    primary_summary = _summarize_primary(primary_cv)
    primary_summary.to_csv(out / "repeated_cv_summary.csv", index=False)

    print("Running Family B leave-one-block-out 5x5 CV...")
    family_b_cv = repeated_cv.run_family_b_repeated_cv(X_train, y_train)
    family_b_cv.to_csv(out / "block_ablation_cv.csv", index=False)

    print("Statistical inference...")
    inference = si.run_inference(primary_cv, family_b_cv)
    inference.to_csv(out / "statistical_inference.csv", index=False)
    si.write_inference_summary(out / "statistical_inference_summary.md", inference)

    # Decision gate context from holdout + primary CV means
    ed_row = holdout_df.loc[holdout_df["model_name"] == "ed_history"].iloc[0]
    five_row = holdout_df.loc[holdout_df["model_name"] == "five_block"].iloc[0]
    six_row = holdout_df.loc[holdout_df["model_name"] == "six_block"].iloc[0]
    best_ed_roc = float(ed_row["roc_auc"])
    best_ed_pr = float(ed_row["pr_auc"])
    full_roc = float(six_row["roc_auc"])
    full_pr = float(six_row["pr_auc"])

    families_present = {
        config.FEATURE_INDEX[c].family for c in six_cols if c in config.FEATURE_INDEX
    }
    color, components = report.decide_gate(
        {
            "usable_n": len(usable),
            "n_outcome_events": n_events,
            "outcome_prevalence": prevalence,
            "families_present": families_present,
            "n_allowed_candidates": len(config.allowed_predictor_specs()),
            "n_present_allowed": len(six_cols),
            "longitudinal_ok": True,
            "leakage_ok": True,
            "calibration_produced": True,
            "unique_persons": True,
            "weighted": False,
            "baseline2_roc_auc": best_ed_roc,
            "full_roc_auc": full_roc,
            "full_pr_auc": full_pr,
            "best_ed_baseline_roc_auc": best_ed_roc,
            "best_ed_baseline_pr_auc": best_ed_pr,
        }
    )

    # SDOH marginal from CV (six - five) for reporting alongside gate
    sdoh_roc_mean = float(primary_cv["delta_roc_six_minus_five"].mean())
    sdoh_pr_mean = float(primary_cv["delta_pr_six_minus_five"].mean())
    a1_roc = inference[
        (inference["contrast_id"] == "A1") & (inference["metric"] == "roc_auc")
    ].iloc[0]
    six_five_roc = inference[
        (inference["contrast_id"] == "C_six_vs_five") & (inference["metric"] == "roc_auc")
    ].iloc[0]
    six_five_pr = inference[
        (inference["contrast_id"] == "C_six_vs_five") & (inference["metric"] == "pr_auc")
    ].iloc[0]
    b6_roc = inference[
        (inference["contrast_id"] == "B6") & (inference["metric"] == "roc_auc")
    ].iloc[0]

    summary = {
        "gate": color,
        "components": components,
        "n_analytic_cohort": len(usable),
        "n_outcome_events": n_events,
        "outcome_prevalence": prevalence,
        "n_train": int(len(y_train)),
        "n_holdout": int(len(y_holdout)),
        "n_predictors_six_block": len(six_cols),
        "holdout": {
            "ed_roc_auc": best_ed_roc,
            "ed_pr_auc": best_ed_pr,
            "five_roc_auc": float(five_row["roc_auc"]),
            "five_pr_auc": float(five_row["pr_auc"]),
            "six_roc_auc": full_roc,
            "six_pr_auc": full_pr,
            "six_minus_ed_roc": full_roc - best_ed_roc,
            "six_minus_ed_pr": full_pr - best_ed_pr,
            "six_minus_five_roc": full_roc - float(five_row["roc_auc"]),
            "six_minus_five_pr": full_pr - float(five_row["pr_auc"]),
            "note": (
                "Locked 25% holdout, seed 42. First-run internal evaluation; "
                "not external validation."
            ),
        },
        "cv_sdoh_marginal_mean": {
            "delta_roc_six_minus_five": sdoh_roc_mean,
            "delta_pr_six_minus_five": sdoh_pr_mean,
        },
        "inference_highlights": {
            "A1_roc_mean_delta": float(a1_roc["mean_delta"]),
            "A1_roc_corrected_se": float(a1_roc["corrected_se"]),
            "A1_roc_p": float(a1_roc["raw_p_value"]),
            "C_six_vs_five_roc_mean_delta": float(six_five_roc["mean_delta"]),
            "C_six_vs_five_roc_p": float(six_five_roc["raw_p_value"]),
            "C_six_vs_five_pr_mean_delta": float(six_five_pr["mean_delta"]),
            "C_six_vs_five_pr_p": float(six_five_pr["raw_p_value"]),
            "B6_roc_mean_delta": float(b6_roc["mean_delta"]),
            "B6_roc_raw_p": float(b6_roc["raw_p_value"]),
            "B6_roc_holm_p": float(b6_roc["holm_adjusted_p_value"]),
        },
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "pre_registration": "docs/pre_registration.md",
    }
    report.write_summary(out / "feasibility_summary.json", summary)

    # Primary CV markdown
    (out / "repeated_cv_summary.md").write_text(
        f"""# Repeated CV summary (training-only 5x5)

Seed: holdout={repeated_cv.HOLDOUT_SEED}, CV={repeated_cv.CV_RANDOM_STATE},
splits={repeated_cv.CV_N_SPLITS}, repeats={repeated_cv.CV_N_REPEATS}.
Training N={len(y_train):,}; holdout unused in CV.

## Mean fold metrics

| Model | ROC-AUC | PR-AUC | Brier |
|---|---:|---:|---:|
| ED-history | {primary_cv['ed_roc_auc'].mean():.4f} | {primary_cv['ed_pr_auc'].mean():.4f} | {primary_cv['ed_brier'].mean():.4f} |
| Five-block | {primary_cv['five_roc_auc'].mean():.4f} | {primary_cv['five_pr_auc'].mean():.4f} | {primary_cv['five_brier'].mean():.4f} |
| Six-block (full) | {primary_cv['six_roc_auc'].mean():.4f} | {primary_cv['six_pr_auc'].mean():.4f} | {primary_cv['six_brier'].mean():.4f} |

## Mean paired deltas

| Contrast | Δ ROC | Δ PR | Δ Brier |
|---|---:|---:|---:|
| Five − ED | {primary_cv['delta_roc_five_minus_ed'].mean():+.4f} | {primary_cv['delta_pr_five_minus_ed'].mean():+.4f} | {primary_cv['delta_brier_five_minus_ed'].mean():+.4f} |
| Six − Five (SDOH) | {primary_cv['delta_roc_six_minus_five'].mean():+.4f} | {primary_cv['delta_pr_six_minus_five'].mean():+.4f} | {primary_cv['delta_brier_six_minus_five'].mean():+.4f} |
| Six − ED (A1) | {primary_cv['delta_roc_six_minus_ed'].mean():+.4f} | {primary_cv['delta_pr_six_minus_ed'].mean():+.4f} | {primary_cv['delta_brier_six_minus_ed'].mean():+.4f} |

Fold-level percentiles are descriptive only. See statistical_inference_summary.md
for Nadeau-Bengio tests.
""",
        encoding="utf-8",
    )

    print(f"Decision gate: {color}")
    print(json.dumps(summary["inference_highlights"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
