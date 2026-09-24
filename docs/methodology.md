# Methodology

Methods narrative for the SDOH-extended Panel 24 feasibility pipeline.
Implementation lives under `feasibility/`. This is a **predictive
research analysis**, not a clinical tool, causal study, or national
risk calculator.

User-supplied HC-245 / HC-233 files were analyzed. The project’s final
status is **inconclusive — underpowered** (see
`docs/results_amendment_2.md` and `docs/limitations.md`). This document
describes the locked methods design; it is not the archival verdict.

---

## 1. Objective

Estimate, on the MEPS Panel 24 SDOH-restricted analytic sample, how much
incremental discrimination a pre-specified pre-cutoff feature set
**including the 2021 SDOH / SHE block** adds beyond three-year ED
history when predicting any ED visit in 2022 — and whether removing the
SDOH block (or other blocks) changes performance under the same CV
design as the companion study.

## 2. Data

- **Required:** HC-245 (Panel 24, 4-year longitudinal, 2019–2022).
- **Optional:** HC-233 (2021 full-year consolidated) for `DUPERSID`
  validation and `SDOHWT21F` provenance.
- SDOH items for Panel 24 are on HC-245 as `SD*5` (Round 5, 2021).
- Details: `docs/data_sources.md`, `docs/linkage_feasibility.md`.

## 3. Cohort

`YEARIND == 1` ∧ valid `ERTOTY1`–`ERTOTY4` ∧ `SDOHELIG5 == 1` ∧ unique
`DUPERSID`. Unweighted analytic sample; survey weights recorded only.

## 4. Cutoff and outcome

Cutoff 2021-12-31; outcome `ERTOTY4 >= 1`. Leakage enforced in
`feasibility/features.py` (raises `LeakageError`).

## 5. Predictors

Five companion blocks plus SDOH (`docs/pre_registration.md`). Feature
audit mirrors the companion: name, family, availability year,
treatment, documentation status, present/usable flags.

## 6. Model and evaluation

L2 logistic (`C=1.0`); 25% holdout seed 42; 5×5 repeated stratified CV
seed 2021 on the training portion; ROC-AUC, PR-AUC, Brier; calibration
written for the full model on the holdout path.

## 7. Inference

Nadeau–Bengio corrected tests; Holm within Family B (B1–B6). Family A
has a single primary contrast (full − ED history).

## 8. Decision gate

Pre-registered floors in `docs/pre_registration.md` and
`feasibility/report.py`. Triage only; not a clinical decision rule.
