"""
Amendment 2 Step 2: EPV for six-block model with SDOH composites.

Same design-matrix / EPV method as docs/dimensionality_diagnostic.md.
If six-block EPV < 10, exit non-zero and do not authorize modeling.
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
    sdoh_composites,
)


EPV_FLOOR = 10.0


def prep_width(X_train: pd.DataFrame, cols: list[str]) -> int:
    present = [c for c in cols if c in X_train.columns]
    num, cat = features.split_columns_by_treatment(present)
    prep = modeling._preprocess(num, cat)
    Xt = prep.fit_transform(X_train[present])
    return int(Xt.shape[1])


def main() -> int:
    files = download.main()
    df = ingest.load_longitudinal(files["longitudinal"])
    usable = longitudinal.usable_prediction_population(df)
    usable = sdoh_composites.add_sdoh_composites(usable)

    # Register composites as numeric FeatureSpecs for leakage/treatment split.
    # Temporary specs for this diagnostic only — mirrored in amendment runner.
    for name in sdoh_composites.COMPOSITE_NAMES:
        if name not in config.FEATURE_INDEX:
            from feasibility.config import FeatureSpec, validate_feature_metadata

            spec = FeatureSpec(
                name=name,
                family="sdoh",
                description=f"Amendment-2 domain composite {name}",
                availability_year=2021,
                time_invariant=False,
                allowed_by_cutoff=True,
                treatment="numeric",
                documentation_status="confirmed",
            )
            validate_feature_metadata(spec)
            config.FEATURE_INDEX[name] = spec

    five_cols = [c for c in repeated_cv.FIVE_BLOCK_COLUMNS if c in usable.columns]
    sdoh_cols = list(sdoh_composites.COMPOSITE_NAMES)
    six_cols = five_cols + sdoh_cols

    X = features.build_feature_matrix(usable, six_cols)
    y = features.build_outcome(usable)["future_ed_visit"].astype(int)
    X_train, _, y_train, _ = repeated_cv.training_portion(X, y)

    w_five = prep_width(X_train, five_cols)
    w_sdoh = prep_width(X_train, sdoh_cols)
    w_six = prep_width(X_train, six_cols)

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
    mean_events = float(np.mean(event_counts))
    epv_five = mean_events / w_five
    epv_six = mean_events / w_six
    clears = epv_six >= EPV_FLOOR

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "# Amendment 2 — EPV diagnostic (SDOH composites)",
        "",
        f"**Date:** {today} (UTC)",
        "**Method:** Same as `docs/dimensionality_diagnostic.md` "
        "(outer train N=2,700 preprocessor fit; inner CV train N from "
        "`repeated_cv_metrics.csv`; EPV = mean CV train events / design columns).",
        "",
        "| Block | Source features | Design-matrix columns |",
        "|---|---:|---:|",
        f"| Five-block | {len(five_cols)} | **{w_five}** |",
        f"| SDOH composites | {len(sdoh_cols)} | **{w_sdoh}** |",
        f"| Six-block (amended) | {len(six_cols)} | **{w_six}** |",
        "",
        f"- Mean CV training fold size: **{mean_cv_train_n:.0f}**",
        f"- Mean CV training events: **{mean_events:.0f}**",
        "",
        "| Model | EPV |",
        "|---|---:|",
        f"| Five-block | **{epv_five:.3f}** |",
        f"| Six-block (amended) | **{epv_six:.3f}** |",
        "",
        f"**EPV floor (amendment Step 2):** >= {EPV_FLOOR:.0f}",
        f"**Clears floor:** {clears}",
        "",
    ]
    if not clears:
        lines.extend(
            [
                "## Stop",
                "",
                f"Amended six-block EPV = {epv_six:.3f} is below the floor of "
                f"{EPV_FLOOR:.0f}. Per `docs/pre_registration_amendment_2.md` "
                "Step 2, **do not proceed to composite-model fitting**.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Proceed",
                "",
                "EPV clears the floor. Amendment composite definitions are locked "
                "for the single Stage-3 rerun.",
                "",
            ]
        )

    out = config.REPO_ROOT / "docs" / "epv_amendment_2.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out.read_text(encoding="utf-8").encode("ascii", "replace").decode("ascii"))
    print(f"Wrote {out}")
    return 0 if clears else 2


if __name__ == "__main__":
    raise SystemExit(main())
