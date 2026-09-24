"""
python -m feasibility.run

End-to-end orchestrator. Fails closed without user-supplied HC-245.
Does not invent metrics when data are absent.
"""
from __future__ import annotations

import dataclasses
import sys

import pandas as pd

from . import (
    config,
    download,
    features,
    ingest,
    linkage,
    longitudinal,
    modeling,
    report,
)


def main() -> int:
    config.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    files = download.main()
    df = ingest.load_longitudinal(files["longitudinal"])
    longitudinal.assert_unique_persons(df)

    sdoh_path = linkage.require_sdoh_on_longitudinal(df)
    pd.DataFrame([sdoh_path]).to_csv(
        config.OUTPUTS_DIR / "sdoh_source_path.csv", index=False
    )

    if "consolidated_2021" in files:
        hc233 = ingest.load_consolidated_optional(files["consolidated_2021"])
        join = linkage.join_report(df, hc233)
        pd.DataFrame([join]).to_csv(
            config.OUTPUTS_DIR / "linkage_join_report.csv", index=False
        )

    dup_check = longitudinal.duplicate_person_check(df)
    usable_df = longitudinal.usable_prediction_population(df)
    cohort = longitudinal.cohort_summary(df, usable_df)
    pd.DataFrame(
        [
            {
                **dup_check,
                **cohort,
                "n_rows": len(df),
                "n_cols": df.shape[1],
            }
        ]
    ).to_csv(config.OUTPUTS_DIR / "population_summary.csv", index=False)

    audit = features.build_feature_audit(usable_df)
    audit.to_csv(config.OUTPUTS_DIR / "feature_audit.csv", index=False)
    usable_cols = features.usable_predictor_columns(audit)
    X = features.build_feature_matrix(usable_df, usable_cols)
    features.assert_no_leakage(list(X.columns))
    outcomes = features.build_outcome(usable_df)
    y = outcomes["future_ed_visit"].astype(int)

    outcome_prevalence = float(y.mean()) if len(y) else 0.0
    n_outcome_events = int(y.sum()) if len(y) else 0

    if len(y) < 40 or y.nunique() < 2:
        summary = {
            "status": "STOPPED_BEFORE_MODELING",
            "reason": (
                "Analytic cohort after SDOH filter is too small or has a "
                "single outcome class; refusing to fit models or invent metrics."
            ),
            "n_analytic_cohort": int(len(usable_df)),
            "n_outcome_events": n_outcome_events,
            "outcome_prevalence": outcome_prevalence,
            "gate": "RED",
        }
        report.write_summary(config.OUTPUTS_DIR / "feasibility_summary.json", summary)
        print(summary["reason"])
        return 2

    X_train, X_test, y_train, y_test = modeling.split_holdout(X, y)
    results = [modeling.baseline_prevalence(y_train, y_test)]

    prior_col = config.ED_VISIT_VARS["year3_2021"]
    if prior_col in X.columns:
        results.append(
            modeling.baseline_prior_year_only(
                X_train, y_train, X_test, y_test, prior_col
            )
        )
    hist_cols = [c for c in config.PREDICTOR_ED_VARS if c in X.columns]
    if hist_cols:
        results.append(
            modeling.baseline_three_year_history(
                X_train, y_train, X_test, y_test, hist_cols
            )
        )

    numeric_cols, categorical_cols = features.split_columns_by_treatment(usable_cols)
    y_prob_full = None
    if numeric_cols or categorical_cols:
        full_result, _pipe, y_prob_full = modeling.full_logistic_model(
            X_train, y_train, X_test, y_test, numeric_cols, categorical_cols
        )
        results.append(full_result)

    pd.DataFrame([dataclasses.asdict(r) for r in results]).to_csv(
        config.OUTPUTS_DIR / "model_metrics.csv", index=False
    )

    calibration_produced = False
    if y_prob_full is not None:
        modeling.write_calibration_outputs(
            y_test,
            y_prob_full,
            config.OUTPUTS_DIR / "calibration.csv",
            config.FIGURES_DIR / "calibration.png",
        )
        calibration_produced = True

    def _metric(name, field):
        row = next((r for r in results if r.model_name == name), None)
        return None if row is None else getattr(row, field)

    ed_baselines = [
        r
        for r in results
        if r.model_name
        in {
            "baseline_2_prior_year_ed_only",
            "baseline_3_three_year_ed_history",
        }
    ]
    best_ed_roc = max(
        (r.roc_auc for r in ed_baselines if r.roc_auc is not None), default=None
    )
    best_ed_pr = max(
        (r.pr_auc for r in ed_baselines if r.pr_auc is not None), default=None
    )

    families_present = {
        config.FEATURE_INDEX[c].family for c in usable_cols if c in config.FEATURE_INDEX
    }
    n_allowed = len(config.allowed_predictor_specs())
    n_present = int(audit["usable"].sum())

    color, components = report.decide_gate(
        {
            "usable_n": len(usable_df),
            "n_outcome_events": n_outcome_events,
            "outcome_prevalence": outcome_prevalence,
            "families_present": families_present,
            "n_allowed_candidates": n_allowed,
            "n_present_allowed": n_present,
            "longitudinal_ok": True,
            "leakage_ok": True,
            "calibration_produced": calibration_produced,
            "unique_persons": dup_check["n_duplicate_person_rows"] == 0,
            "weighted": False,
            "baseline2_roc_auc": _metric("baseline_2_prior_year_ed_only", "roc_auc"),
            "full_roc_auc": _metric("full_logistic", "roc_auc"),
            "full_pr_auc": _metric("full_logistic", "pr_auc"),
            "best_ed_baseline_roc_auc": best_ed_roc,
            "best_ed_baseline_pr_auc": best_ed_pr,
        }
    )

    summary = {
        "gate": color,
        "components": components,
        "cohort": cohort,
        "n_predictors": len(usable_cols),
        "families_present": sorted(families_present),
        "note": (
            "Holdout metrics only on this path. Repeated CV, block ablation, "
            "and Nadeau-Bengio inference are separate stages to be run after "
            "data adequacy is confirmed — see docs/pre_registration.md."
        ),
    }
    report.write_summary(config.OUTPUTS_DIR / "feasibility_summary.json", summary)
    print(f"Decision gate: {color}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
