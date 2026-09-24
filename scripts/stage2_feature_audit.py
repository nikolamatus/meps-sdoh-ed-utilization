"""Stage 2: feature audit + live leakage-guard injection test."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from feasibility import config, download, features, ingest, longitudinal
from feasibility.features import LeakageError


def main() -> int:
    files = download.main()
    df = ingest.load_longitudinal(files["longitudinal"])
    longitudinal.assert_unique_persons(df)
    usable = longitudinal.usable_prediction_population(df)

    audit = features.build_feature_audit(usable)
    config.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    audit.to_csv(config.OUTPUTS_DIR / "feature_audit.csv", index=False)

    usable_cols = features.usable_predictor_columns(audit)
    features.assert_no_leakage(usable_cols)
    X = features.build_feature_matrix(usable, usable_cols)
    features.assert_no_leakage(list(X.columns))

    expected_blocks = {
        "age": ["AGEY3X"],
        "demographics": ["SEX", "RACETHX", "REGIONY3", "MARRY6X"],
        "health_status": ["RTHLTH6", "MNHLTH6"],
        "access": ["INSCOVY3", "HAVEUS6"],
        "socioeconomic": ["POVCATY3", "TTLPY3X", "EMPST6"],
        "prior_utilization": list(config.PREDICTOR_ED_VARS),
        "sdoh": config.sdoh_predictor_names(),
    }
    block_status = []
    for block, names in expected_blocks.items():
        present = [n for n in names if n in usable.columns]
        usable_in_x = [n for n in names if n in usable_cols]
        block_status.append(
            {
                "block": block,
                "n_expected": len(names),
                "n_present_on_file": len(present),
                "n_usable_in_X": len(usable_in_x),
                "missing_on_file": ",".join(
                    n for n in names if n not in usable.columns
                ),
            }
        )
    block_df = pd.DataFrame(block_status)
    block_df.to_csv(config.OUTPUTS_DIR / "feature_block_presence.csv", index=False)

    injection_caught = False
    injection_error = ""
    try:
        features.build_feature_matrix(usable, usable_cols + ["ERTOTY4"])
    except LeakageError as exc:
        injection_caught = True
        injection_error = str(exc)

    injection2_caught = False
    injection2_error = ""
    try:
        features.assert_no_leakage(usable_cols + ["AGEY4X"])
    except LeakageError as exc:
        injection2_caught = True
        injection2_error = str(exc)

    gate2_pass = injection_caught and injection2_caught
    n_allowed = len(config.allowed_predictor_specs())
    n_usable = len(usable_cols)
    families = sorted(
        {
            config.FEATURE_INDEX[c].family
            for c in usable_cols
            if c in config.FEATURE_INDEX
        }
    )

    summary = {
        "n_analytic_cohort": len(usable),
        "n_allowed_candidates": n_allowed,
        "n_usable_predictors": n_usable,
        "present_allowed_fraction": n_usable / n_allowed if n_allowed else None,
        "families_in_X": ",".join(families),
        "leakage_guard_clean_set_ok": True,
        "injection_ertoty4_caught": injection_caught,
        "injection_agey4x_caught": injection2_caught,
        "gate2_pass": gate2_pass,
        "injection_ertoty4_message": injection_error,
        "injection_agey4x_message": injection2_error,
    }
    pd.DataFrame([summary]).to_csv(
        config.OUTPUTS_DIR / "feature_audit_gate2.csv", index=False
    )

    md = f"""# Feature audit (Stage 2)

Ran {datetime.now(timezone.utc).isoformat()} on the dual analytic cohort
(N={len(usable):,}).

## Usable predictors

- Allowed candidates (config): {n_allowed}
- Usable on this file: {n_usable}
- Present/allowed fraction: {summary['present_allowed_fraction']:.3f}
- Families in X: {summary['families_in_X']}

## Block presence

```
{block_df.to_string(index=False)}
```

## Leakage guard live test (Gate 2)

| Injection | Caught | Message |
|---|---|---|
| ERTOTY4 added to X | {injection_caught} | {injection_error} |
| AGEY4X asserted in columns | {injection2_caught} | {injection2_error} |

**Gate 2: {"PASS" if gate2_pass else "FAIL"}**
"""
    (config.OUTPUTS_DIR / "feature_audit_summary.md").write_text(md, encoding="utf-8")
    print(md)
    if not gate2_pass:
        print("STOP: Gate 2 failed")
        return 2
    print("Gate 2 passed - may proceed to Stage 3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
