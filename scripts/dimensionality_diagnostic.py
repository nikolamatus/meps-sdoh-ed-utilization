"""
Read-only dimensionality diagnostic for the SDOH block.

Fits only the existing preprocessing ColumnTransformer (no classifier,
no C change). Writes docs/dimensionality_diagnostic.md and exits.
"""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold

from feasibility import (
    config,
    download,
    features,
    ingest,
    longitudinal,
    modeling,
    repeated_cv,
)


def prep_matrix(X_train: pd.DataFrame, cols: list[str]) -> dict:
    present = [c for c in cols if c in X_train.columns]
    num, cat = features.split_columns_by_treatment(present)
    prep = modeling._preprocess(num, cat)
    Xt = prep.fit_transform(X_train[present])
    cat_detail = []
    if cat:
        ohe = prep.named_transformers_["cat"].named_steps["onehot"]
        for name, cats in zip(cat, ohe.categories_):
            cat_detail.append(
                {
                    "feature": name,
                    "n_levels_encoded": int(len(cats)),
                    "levels": [str(x) for x in cats],
                }
            )
    return {
        "n_source_features": len(present),
        "n_numeric": len(num),
        "n_categorical": len(cat),
        "n_design_columns": int(Xt.shape[1]),
        "numeric_names": num,
        "cat_detail": cat_detail,
    }


def main() -> int:
    files = download.main()
    df = ingest.load_longitudinal(files["longitudinal"])
    usable = longitudinal.usable_prediction_population(df)

    six_cols = [c for c in repeated_cv.SIX_BLOCK_COLUMNS if c in usable.columns]
    five_cols = [c for c in repeated_cv.FIVE_BLOCK_COLUMNS if c in usable.columns]
    sdoh_cols = [c for c in config.sdoh_predictor_names() if c in usable.columns]

    X = features.build_feature_matrix(usable, six_cols)
    y = features.build_outcome(usable)["future_ed_visit"].astype(int)
    X_train, _X_ho, y_train, _y_ho = repeated_cv.training_portion(X, y)

    five = prep_matrix(X_train, five_cols)
    sdoh = prep_matrix(X_train, sdoh_cols)
    six = prep_matrix(X_train, six_cols)

    cv = pd.read_csv(config.OUTPUTS_DIR / "repeated_cv_metrics.csv")
    mean_cv_train_n = float(cv["n_cv_train"].mean())

    splitter = RepeatedStratifiedKFold(
        n_splits=repeated_cv.CV_N_SPLITS,
        n_repeats=repeated_cv.CV_N_REPEATS,
        random_state=repeated_cv.CV_RANDOM_STATE,
    )
    Xtr = X_train.reset_index(drop=True)
    ytr = pd.Series(np.asarray(y_train), name="y")
    event_counts = [
        int(ytr.iloc[tr_idx].sum()) for tr_idx, _ in splitter.split(Xtr, ytr)
    ]
    mean_cv_train_events = float(np.mean(event_counts))

    epv_five = mean_cv_train_events / five["n_design_columns"]
    epv_six = mean_cv_train_events / six["n_design_columns"]

    sdoh_cat_cols = sum(d["n_levels_encoded"] for d in sdoh["cat_detail"])
    sum_ok = five["n_design_columns"] + sdoh["n_design_columns"] == six["n_design_columns"]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "# Dimensionality diagnostic (SDOH block)",
        "",
        f"**Date:** {today} (UTC)",
        "**Scope:** Read-only diagnostic. No models were retrained or retuned.",
        "**Method:** Reconstruct the locked holdout training portion (seed 42),",
        "fit only the existing `ColumnTransformer` preprocessing used by",
        "`feasibility.modeling._preprocess` (median/mode imputation + scaling +",
        "one-hot encoding), and count design-matrix columns. The classifier and",
        "`C` were not fit for this diagnostic.",
        "",
        "This note does not reinterpret prior significance tests or gate results.",
        "",
        "---",
        "",
        "## 1. Design-matrix width (post-imputation, post-encoding)",
        "",
        f"Preprocessor fitted on the outer training portion (N = {len(y_train):,}).",
        "",
        "| Model / block | Source features | Numeric | Categorical | **Design-matrix columns** |",
        "|---|---:|---:|---:|---:|",
        (
            f"| (a) Five-block full | {five['n_source_features']} | "
            f"{five['n_numeric']} | {five['n_categorical']} | "
            f"**{five['n_design_columns']}** |"
        ),
        (
            f"| (b) SDOH block alone | {sdoh['n_source_features']} | "
            f"{sdoh['n_numeric']} | {sdoh['n_categorical']} | "
            f"**{sdoh['n_design_columns']}** |"
        ),
        (
            f"| (c) Six-block full | {six['n_source_features']} | "
            f"{six['n_numeric']} | {six['n_categorical']} | "
            f"**{six['n_design_columns']}** |"
        ),
        "",
        (
            f"Five + SDOH design columns sum to "
            f"{five['n_design_columns'] + sdoh['n_design_columns']} "
            f"(equals six-block width {six['n_design_columns']}: {sum_ok})."
        ),
        "",
        "### SDOH block breakdown (48 pre-registered items)",
        "",
        (
            f"- Numeric source features: **{len(sdoh['numeric_names'])}**"
            + (
                f" ({', '.join('`' + n + '`' for n in sdoh['numeric_names'])})"
                if sdoh["numeric_names"]
                else " (none)"
            )
        ),
        f"- Categorical source features: **{len(sdoh['cat_detail'])}**",
        (
            f"- Design columns from SDOH categoricals "
            f"(sum of one-hot levels): **{sdoh_cat_cols}**"
        ),
        f"- Design columns from SDOH numerics: **{len(sdoh['numeric_names'])}**",
        f"- Total SDOH design columns: **{sdoh['n_design_columns']}**",
        "",
        "| SDOH feature | Treatment | One-hot levels (columns contributed) |",
        "|---|---|---:|",
    ]
    for d in sdoh["cat_detail"]:
        lines.append(
            f"| `{d['feature']}` | categorical | {d['n_levels_encoded']} |"
        )
    for n in sdoh["numeric_names"]:
        lines.append(f"| `{n}` | numeric | 1 |")

    lines.extend(
        [
            "",
            "One-hot encoding uses `OneHotEncoder(handle_unknown=\"ignore\")` with no",
            "category drop; each observed training level becomes one column.",
            "",
            "---",
            "",
            "## 2. Events-per-variable (EPV)",
            "",
            "Using the **already saved** training-only 5x5 CV fold sizes from",
            "`outputs/repeated_cv_metrics.csv` (fold sizes not re-estimated from new",
            "model fits):",
            "",
            (
                f"- Mean CV training fold size: **{mean_cv_train_n:.0f}** "
                "(all 25 folds identical). This is the *inner* CV train size on the "
                "outer 75% training portion of 2,700 — not ~2,880."
            ),
            (
                f"- Mean CV training event count: **{mean_cv_train_events:.0f}** "
                "(exact fold event counts reconstructed with the same "
                f"`RepeatedStratifiedKFold` seed {repeated_cv.CV_RANDOM_STATE}; "
                f"unique values = {sorted(set(event_counts))})."
            ),
            "",
            "EPV = (mean CV training events) / (design-matrix columns).",
            "",
            "| Model | Design columns | Mean train events | **EPV** |",
            "|---|---:|---:|---:|",
            (
                f"| Five-block | {five['n_design_columns']} | "
                f"{mean_cv_train_events:.0f} | **{epv_five:.3f}** |"
            ),
            (
                f"| Six-block | {six['n_design_columns']} | "
                f"{mean_cv_train_events:.0f} | **{epv_six:.3f}** |"
            ),
            "",
            "---",
            "",
            "## Notes",
            "",
            "- No change to `modeling.py`, `config.py`, `C`, or previously reported",
            "  performance numbers.",
            "- Outer training N for the preprocessor fit in section 1 is 2,700",
            "  (holdout seed 42).",
            "- Inner CV train N for EPV in section 2 is 2,160 per fold.",
            "",
        ]
    )

    path = config.REPO_ROOT / "docs" / "dimensionality_diagnostic.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path}")
    print(
        f"five={five['n_design_columns']} sdoh={sdoh['n_design_columns']} "
        f"six={six['n_design_columns']} EPV_five={epv_five:.3f} EPV_six={epv_six:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
