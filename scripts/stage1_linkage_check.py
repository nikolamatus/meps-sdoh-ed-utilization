"""Stage 0 provenance enrichment + Stage 1 dual-cohort linkage check."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

from feasibility import config, download, features, ingest, linkage, longitudinal


def main() -> int:
    # --- Stage 0: enrich provenance with documented release labels ---
    prov_path = config.DATA_RAW_DIR / "provenance.json"
    files = download.main()
    prov = json.loads(prov_path.read_text(encoding="utf-8"))
    release_notes = {
        "HC-245": {
            "documented_release": "November 2024",
            "source": "docs/data_sources.md / AHRQ HC-245 download page",
        },
        "HC-233": {
            "documented_release": "August 2023",
            "source": (
                "docs/data_sources.md / AHRQ HC-233 download page "
                "(HC-228 replaced by HC-233)"
            ),
        },
    }
    for f in prov["files"]:
        f.update(release_notes.get(f["puf_id"], {}))
    prov["stage0_schema_check_utc"] = datetime.now(timezone.utc).isoformat()
    prov_path.write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print("PROVENANCE UPDATED")
    for f in prov["files"]:
        print(
            f"  {f['file_name']}: {f['file_size_bytes']:,} bytes "
            f"sha256={f['sha256'][:16]}... release={f.get('documented_release')}"
        )

    df = ingest.load_longitudinal(files["longitudinal"])
    longitudinal.assert_unique_persons(df)
    print(f"HC-245 shape: {df.shape}")
    print(f"DUPERSID unique: {df[config.PERSON_ID].nunique()} rows={len(df)}")

    hc233 = ingest.load_consolidated_optional(files["consolidated_2021"])
    print(f"HC-233 shape: {hc233.shape}")

    n_raw = len(df)
    n_yearind = int(longitudinal.yearind_all_four_years(df).sum())
    n_valid_ed = int(longitudinal.valid_ed_all_four_years(df).sum())
    n_sdoh = int(longitudinal.sdoh_has_data(df).sum())
    companion = longitudinal.companion_prediction_population(df)
    usable = longitudinal.usable_prediction_population(df)
    n_companion = len(companion)
    n_dual = len(usable)

    print("\n=== STAGE 1 COUNTS ===")
    print(f"n_raw={n_raw}")
    print(f"n_yearind==1={n_yearind}")
    print(f"n_valid_ed_all4={n_valid_ed}")
    print(f"n_companion YEARIND+validED={n_companion}")
    print(f"n_SDOHELIG5==1={n_sdoh}")
    print(f"n_dual_cohort={n_dual}")

    ok_companion = n_companion == 5108
    ok_sdoh = n_sdoh == 3640
    print(f"companion==5108? {ok_companion} (got {n_companion})")
    print(f"sdoh==3640? {ok_sdoh} (got {n_sdoh})")

    out = features.build_outcome(usable)
    y = out["future_ed_visit"].dropna().astype(int)
    n_events = int(y.sum())
    prev = float(y.mean()) if len(y) else None
    print(f"dual events={n_events} prevalence={prev}")

    join = linkage.join_report(df, hc233)
    print("\n=== LINKAGE JOIN ===")
    for k, v in join.items():
        print(f"  {k}: {v}")

    p24 = linkage.panel24_subset(hc233)
    sdoh_pairs = []
    for name5 in config.sdoh_predictor_names():
        stem = name5[:-1] if name5.endswith("5") else name5
        candidates = [stem]
        if name5 == "SDPROBSMKDE5":
            candidates = ["SDPROBSMKDET", "SDPROBSMKDE"]
        hc233_name = next((c for c in candidates if c in p24.columns), None)
        if hc233_name is None or name5 not in df.columns:
            sdoh_pairs.append(
                {
                    "hc245": name5,
                    "hc233": hc233_name,
                    "status": "missing_on_one_side",
                }
            )
            continue
        m = df[[config.PERSON_ID, name5]].merge(
            p24[[config.PERSON_ID, hc233_name]].rename(
                columns={hc233_name: "hc233_val"}
            ),
            on=config.PERSON_ID,
            how="inner",
        )
        a = pd.to_numeric(m[name5], errors="coerce")
        b = pd.to_numeric(m["hc233_val"], errors="coerce")
        both = a.notna() & b.notna()
        n_both = int(both.sum())
        n_agree = int((a[both] == b[both]).sum()) if n_both else 0
        n_disagree = n_both - n_agree
        sdoh_pairs.append(
            {
                "hc245": name5,
                "hc233": hc233_name,
                "status": "compared",
                "n_overlapping_ids": len(m),
                "n_both_nonmissing": n_both,
                "n_agree": n_agree,
                "n_disagree": n_disagree,
                "agreement_rate": (n_agree / n_both) if n_both else None,
            }
        )

    pairs_df = pd.DataFrame(sdoh_pairs)
    print("\n=== SDOH VALUE CROSS-CHECK ===")
    print(f"items compared: {(pairs_df.status == 'compared').sum()}")
    print(
        "items with any disagreement: "
        f"{((pairs_df.status == 'compared') & (pairs_df.n_disagree > 0)).sum()}"
    )

    wt_info: dict = {}
    if "SDOHWT21F" in p24.columns:
        mwt = df[[config.PERSON_ID, config.SDOH_ELIG]].merge(
            p24[[config.PERSON_ID, "SDOHWT21F", "SDOHELIG"]],
            on=config.PERSON_ID,
            how="inner",
        )
        wt = pd.to_numeric(mwt["SDOHWT21F"], errors="coerce")
        elig5 = pd.to_numeric(mwt[config.SDOH_ELIG], errors="coerce")
        wt_info = {
            "n_overlap_with_weight_col": len(mwt),
            "n_positive_SDOHWT21F": int((wt > 0).sum()),
            "n_SDOHELIG5_eq1_and_positive_wt": int(((elig5 == 1) & (wt > 0)).sum()),
            "n_SDOHELIG5_eq1_and_zero_wt": int(((elig5 == 1) & (wt == 0)).sum()),
            "n_SDOHELIG5_eq1_on_overlap": int((elig5 == 1).sum()),
        }
        print("\n=== SDOHWT21F ===")
        print(wt_info)

    min_n = 1500  # docs/pre_registration.md
    gate1_pass = n_dual >= min_n
    print(f"\n=== GATE 1 === dual_N={n_dual} threshold={min_n} PASS={gate1_pass}")

    if not ok_companion:
        print("STOP: companion N discrepancy vs expected 5,108")
    if not ok_sdoh:
        print("STOP: SDOHELIG5==1 discrepancy vs expected 3,640")

    config.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = [
        {"metric": "n_raw_hc245", "value": n_raw},
        {"metric": "n_yearind_eq1", "value": n_yearind},
        {"metric": "n_valid_ed_all_four_years", "value": n_valid_ed},
        {
            "metric": "n_companion_yearind_and_valid_ed",
            "value": n_companion,
            "expected": 5108,
            "matches_expected": ok_companion,
        },
        {
            "metric": "n_sdoh_elig5_eq1_full_hc245",
            "value": n_sdoh,
            "expected": 3640,
            "matches_expected": ok_sdoh,
        },
        {"metric": "n_dual_cohort", "value": n_dual},
        {"metric": "n_dual_outcome_events", "value": n_events},
        {"metric": "dual_outcome_prevalence", "value": prev},
        {"metric": "gate1_min_usable_n", "value": min_n},
        {"metric": "gate1_pass", "value": int(gate1_pass)},
    ]
    for k, v in join.items():
        rows.append({"metric": f"join_{k}", "value": v})
    for k, v in wt_info.items():
        rows.append({"metric": f"weight_{k}", "value": v})
    pd.DataFrame(rows).to_csv(config.OUTPUTS_DIR / "linkage_check.csv", index=False)
    pairs_df.to_csv(
        config.OUTPUTS_DIR / "linkage_sdoh_value_concordance.csv", index=False
    )

    disagree_items = pairs_df[
        (pairs_df.status == "compared") & (pairs_df.n_disagree > 0)
    ]
    mean_agree = pairs_df.loc[
        pairs_df.status == "compared", "agreement_rate"
    ].mean()
    md = f"""# Linkage check (Stage 1)

Computed from user-supplied `h245.dta` and `h233.dta` on
{datetime.now(timezone.utc).isoformat()}.

## Dual-cohort counts (HC-245)

| Metric | Value | Expected | Match |
|---|---:|---:|---|
| Raw HC-245 persons | {n_raw:,} | 5,565 | {n_raw == 5565} |
| YEARIND==1 | {n_yearind:,} | 5,108 | {n_yearind == 5108} |
| Valid ERTOTY1-Y4 | {n_valid_ed:,} | — | — |
| Companion cohort (YEARIND==1 and valid ED) | {n_companion:,} | **5,108** | **{ok_companion}** |
| SDOHELIG5==1 (full file) | {n_sdoh:,} | **3,640** | **{ok_sdoh}** |
| **Dual cohort (companion and SDOHELIG5==1)** | **{n_dual:,}** | — | — |
| Dual-cohort ED events (ERTOTY4>=1) | {n_events:,} | — | — |
| Dual-cohort prevalence | {prev:.4f} | — | — |

## Gate 1

Pre-registered minimum usable N: **{min_n:,}**
Dual-cohort N: **{n_dual:,}**
**Gate 1: {"PASS" if gate1_pass else "FAIL"}**

## HC-233 <-> HC-245 DUPERSID join (Panel 24 subset)

| Metric | Value |
|---|---:|
| HC-245 persons | {join['n_hc245']:,} |
| HC-233 Panel 24 persons | {join['n_hc233_panel24']:,} |
| Matched DUPERSID | {join['n_matched_dupersid']:,} |
| Match rate of HC-245 | {join['match_rate_of_hc245']:.4f} |
| SDOHELIG vs SDOHELIG5 agreement (non-missing) | {join['sdoh_elig_agreement_rate']} |

## SDOH item value concordance (overlapping Panel 24 IDs)

Compared items: {(pairs_df.status == 'compared').sum()}
Items with >=1 disagreement: {len(disagree_items)}
Mean agreement rate (compared items): {mean_agree:.6f}

HC-245 remains the primary analysis file. HC-233 is validation/provenance only.
"""
    (config.OUTPUTS_DIR / "linkage_check_summary.md").write_text(md, encoding="utf-8")
    print("\nWrote outputs/linkage_check.csv and linkage_check_summary.md")

    if not ok_companion or not ok_sdoh:
        return 2
    if not gate1_pass:
        print("STOP: Gate 1 failed — do not proceed to Stage 2")
        return 3
    print("Gate 1 passed — may proceed to Stage 2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
