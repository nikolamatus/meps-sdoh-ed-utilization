# Pre-registration: SDOH-extended ED-utilization contrasts

**Date committed:** 2026-09-23  
**Status:** locked before any model is trained on real MEPS microdata  
**Depends on:** `docs/linkage_feasibility.md` (Task 1) — linkage feasible
on HC-245; exact dual-cohort N deferred until files are supplied  

This document is written **before** any model fit on user-supplied
MEPS files. No result, contrast definition, cohort rule, metric, or
inferential procedure in this document may be revised after seeing
fitted scores. If a change is needed later, it must be logged as a
dated amendment with a reason, not a silent edit.

---

## Research question

Does the 2021 MEPS SDOH / SHE instrument add predictive discrimination
for any 2022 ED visit (`ERTOTY4 >= 1`) beyond the five predictor blocks
already used in the companion Panel 24 study (demographics including
age, health status, access, socioeconomic status, and ED history)?

---

## Cohort definition

Analytic cohort (all must hold):

1. Unique `DUPERSID` on HC-245 (duplicates fail the run).
2. `YEARIND == 1` (in file for calendar years 2019–2022).
3. Valid non-sentinel `ERTOTY1`, `ERTOTY2`, `ERTOTY3`, `ERTOTY4`.
4. **`SDOHELIG5 == 1`** (eligible for SDOH and has SDOH data).

`ALL9RDS` is recorded and reported; it is **not** an inclusion
criterion. `LONGWT`, `VARSTR`, `VARPSU` (and `SDOHWT21F` if HC-233 is
joined) are recorded and **not** applied to sklearn metrics.

This cohort is adults with a 2021 SDOH record by construction of
`SDOHELIG5`. It is a subset of the companion all-age cohort.

---

## Outcome

Identical to the companion study:

> `future_ed_visit = 1` if `ERTOTY4 >= 1`, else 0.

`ERTOTY4` never enters `X`. A secondary construct `ERTOTY4 >= 2` may be
counted for inspection only and is **not** modeled in this pass.

---

## Prediction cutoff

- Cutoff: **2021-12-31**
- Outcome window: calendar year **2022**
- SDOH Round-5 (`SD*5`) items are treated as 2021 (allowed).
- Round 7 / Y4 / Round 8–9 variables remain banned.
- Unknown temporal availability fails closed (not used).

---

## Six predictor blocks

| Block ID | Family | Variables |
|---|---|---|
| Age | demographics (age alone for leave-one-out) | `AGEY3X` |
| Demographics | demographics (non-age) | `SEX`, `RACETHX`, `REGIONY3`, `MARRY6X` |
| Health status | health_status | `RTHLTH6`, `MNHLTH6` |
| Access | access | `INSCOVY3`, `HAVEUS6` |
| Socioeconomic | socioeconomic | `POVCATY3`, `TTLPY3X`, `EMPST6` |
| Prior ED | prior_utilization | `ERTOTY1`, `ERTOTY2`, `ERTOTY3` |
| **SDOH (new)** | **sdoh** | All **Include**-marked `SD*5` items in `docs/linkage_feasibility.md` §5.2–§5.8 (housing, food, transportation, financial strain, social support, personal safety, ACEs) |

Excluded SHE items (`SDLIFE5`, `SDMEDCARE5`, `SDPARKS5`, exercise,
stress, e-nicotine, discrimination battery) stay out of the primary
SDOH block as locked in Task 1.

**Full model** = age + demographics + health + access + SES + prior ED
+ SDOH.

Sentinel handling matches the companion: documented MEPS negatives and
**any other negative** → missing; median/mode imputation inside each
training fold only.

---

## Contrast families

### Family A — primary (one hypothesis)

| ID | Contrast | Multiplicity |
|---|---|---|
| A1 | Full model − ED-history baseline | None (sole primary) |

ED-history baseline predictors: `ERTOTY1`, `ERTOTY2`, `ERTOTY3` only.

### Family B — secondary (leave-one-block-out vs full)

Holm–Bonferroni within this family only.

| ID | Block removed |
|---|---|
| B1 | Age (`AGEY3X`) |
| B2 | Demographics (`SEX`, `RACETHX`, `REGIONY3`, `MARRY6X`) |
| B3 | Health (`RTHLTH6`, `MNHLTH6`) |
| B4 | Access (`INSCOVY3`, `HAVEUS6`) |
| B5 | SES (`POVCATY3`, `TTLPY3X`, `EMPST6`) |
| **B6** | **SDOH (all primary `SD*5` items)** |

Family B therefore has **six** contrasts (companion had five; SDOH
adds B6). Holm adjustment is over these six p-values.

Paired descriptive contrasts vs ED-history for each reduced model may
be reported for continuity; they are **not** additional Family B
hypotheses.

---

## Estimator, split, CV

Locked to match the companion implementation:

| Setting | Value |
|---|---|
| Model | L2-regularized logistic regression, `C=1.0`, `max_iter=2000` |
| Preprocessing | Median (numeric) / most-frequent (categorical) imputation, scaling, one-hot encoding — fit inside each training fold |
| Holdout | 25% person-level stratified holdout, `random_state=42`; confirmation only |
| Repeated CV | `RepeatedStratifiedKFold`, `n_splits=5`, `n_repeats=5`, `random_state=2021`, on the training portion only |
| Hyperparameter search | None |
| Survey weights | Not applied |

---

## Metrics

Per fold, for every contrast:

- ROC-AUC
- PR-AUC
- Brier score

Fold-level mean/SD/percentiles remain **descriptive**. The 25 folds are
not treated as 25 independent observations.

---

## Statistical inference

After fold-level CSVs exist for A1 and B1–B6:

1. **Nadeau–Bengio** corrected variance for 5×5 repeated CV on each
   contrast.
2. Family A (A1): Nadeau–Bengio only; no multiplicity adjustment.
3. Family B (B1–B6): Nadeau–Bengio on each, then **Holm–Bonferroni**
   across the six Family B p-values.

No significance testing before the fold-level artifacts exist. No
refitting at the statistical-pass stage.

---

## Decision-gate thresholds (set before seeing real numbers)

Engineering/research triage only — not a validated clinical rule.
Evaluated on the **SDOH-restricted** analytic cohort after the first
full pipeline run with real files.

| Floor | Threshold |
|---|---|
| Usable N | ≥ **1,500** |
| Primary-outcome events | ≥ **100** |
| Outcome prevalence | ≥ **0.03** |
| Prior-ED baseline ROC-AUC | ≥ **0.55** |
| Full − best ED-history ROC-AUC lift | ≥ **0.02** |
| Full − best ED-history PR-AUC lift | ≥ **0.01** |
| Present allowed predictors | ≥ 60% of allowed candidates present on file |
| Required families in X | `prior_utilization`, `demographics`, and at least one of `{health_status, access, socioeconomic}`, plus **`sdoh`** |
| Leakage / unique persons / cohort rule | Must pass |

**Usable N floor note:** lowered from the companion’s 2,000 to 1,500
**before seeing data**, because Task 1 shows SDOH completion caps the
HC-245 SDOH-positive count at 3,640 and the dual filter will reduce it
further. If even 1,500 is not met, the gate fails on data adequacy
rather than inventing a post-hoc threshold.

**GREEN** requires data floors + baseline floor + incremental lifts +
readiness checks. Prior-ED AUC alone never yields GREEN.  
**YELLOW** / **RED** follow the companion gate structure when
incremental value or readiness fails.

No GREEN/YELLOW/RED call is made from architecture alone.

---

## Execution order (after files arrive)

1. Provenance + ingest HC-245 (optional HC-233 linkage report).
2. Dual cohort construction; write population tables (**stop and
   inspect N/events before claiming feasibility**).
3. Feature audit including SDOH; leakage guard.
4. Holdout baselines + full model (structural run).
5. Repeated CV + block ablations A1, B1–B6.
6. Nadeau–Bengio + Holm pass on saved folds.
7. Decision gate + limitations review.

---

## What this document does not claim

No causal claims, no clinical utility, no “avoidable/preventable” ED
use, no national representativeness from unweighted metrics, no
external validation, no authorization to drop or transform predictors
after seeing results.

---

## Amendment log

*(none at commitment date 2026-09-23)*
