# Dimensionality diagnostic (SDOH block)

**Date:** 2026-09-24 (UTC)
**Scope:** Read-only diagnostic. No models were retrained or retuned.
**Method:** Reconstruct the locked holdout training portion (seed 42),
fit only the existing `ColumnTransformer` preprocessing used by
`feasibility.modeling._preprocess` (median/mode imputation + scaling +
one-hot encoding), and count design-matrix columns. The classifier and
`C` were not fit for this diagnostic.

This note does not reinterpret prior significance tests or gate results.

---

## 1. Design-matrix width (post-imputation, post-encoding)

Preprocessor fitted on the outer training portion (N = 2,700).

| Model / block | Source features | Numeric | Categorical | **Design-matrix columns** |
|---|---:|---:|---:|---:|
| (a) Five-block full | 15 | 5 | 10 | **49** |
| (b) SDOH block alone | 48 | 0 | 48 | **183** |
| (c) Six-block full | 63 | 5 | 58 | **232** |

Five + SDOH design columns sum to 232 (equals six-block width 232: True).

### SDOH block breakdown (48 pre-registered items)

- Numeric source features: **0** (none)
- Categorical source features: **48**
- Design columns from SDOH categoricals (sum of one-hot levels): **183**
- Design columns from SDOH numerics: **0**
- Total SDOH design columns: **183**

| SDOH feature | Treatment | One-hot levels (columns contributed) |
|---|---|---:|
| `SDAFRDHOME5` | categorical | 6 |
| `SDHOME5` | categorical | 7 |
| `SDLATERENT5` | categorical | 3 |
| `SDLATEUTIL5` | categorical | 3 |
| `SDSHUTUTIL5` | categorical | 4 |
| `SDPROBPEST5` | categorical | 2 |
| `SDPROBMOLD5` | categorical | 2 |
| `SDPROBLEAD5` | categorical | 2 |
| `SDPROBHEAT5` | categorical | 2 |
| `SDPROBCOOK5` | categorical | 2 |
| `SDPROBSMKDE5` | categorical | 2 |
| `SDPROBLEAKS5` | categorical | 2 |
| `SDPROBNONE5` | categorical | 2 |
| `SDWRRYFD5` | categorical | 3 |
| `SDNOFOOD5` | categorical | 3 |
| `SDHLTHFOOD5` | categorical | 7 |
| `SDNOTRANS5` | categorical | 2 |
| `SDPUBTRANS5` | categorical | 5 |
| `SDPAYBASICS5` | categorical | 4 |
| `SDUNEXPEXP5` | categorical | 4 |
| `SDMISSCCLN5` | categorical | 2 |
| `SDDEBT5` | categorical | 2 |
| `SDFAMILY5` | categorical | 7 |
| `SDFRIENDS5` | categorical | 4 |
| `SDCOMM5` | categorical | 4 |
| `SDTLKPHN5` | categorical | 7 |
| `SDGETTGT5` | categorical | 7 |
| `SDCHURCH5` | categorical | 7 |
| `SDCLUBORG5` | categorical | 7 |
| `SDCOMPAN5` | categorical | 4 |
| `SDLEFTOUT5` | categorical | 5 |
| `SDISOL5` | categorical | 4 |
| `SDSFCRIME5` | categorical | 6 |
| `SDPHYSHURT5` | categorical | 5 |
| `SDINSULT5` | categorical | 6 |
| `SDTHRHARM5` | categorical | 5 |
| `SDSCREAM5` | categorical | 5 |
| `SDHMDEPR5` | categorical | 2 |
| `SDHMALC5` | categorical | 2 |
| `SDHMDRG5` | categorical | 2 |
| `SDHMJAIL5` | categorical | 2 |
| `SDHMDIV5` | categorical | 3 |
| `SDHMBEAT5` | categorical | 3 |
| `SDHURTCHLD5` | categorical | 3 |
| `SDINSCHLD5` | categorical | 3 |
| `SDTCHCHLD5` | categorical | 3 |
| `SDTCHADLT5` | categorical | 3 |
| `SDFRCSXCH5` | categorical | 3 |

One-hot encoding uses `OneHotEncoder(handle_unknown="ignore")` with no
category drop; each observed training level becomes one column.

---

## 2. Events-per-variable (EPV)

Using the **already saved** training-only 5x5 CV fold sizes from
`outputs/repeated_cv_metrics.csv` (fold sizes not re-estimated from new
model fits):

- Mean CV training fold size: **2160** (all 25 folds identical). This is the *inner* CV train size on the outer 75% training portion of 2,700 — not ~2,880.
- Mean CV training event count: **348** (exact fold event counts reconstructed with the same `RepeatedStratifiedKFold` seed 2021; unique values = [348]).

EPV = (mean CV training events) / (design-matrix columns).

| Model | Design columns | Mean train events | **EPV** |
|---|---:|---:|---:|
| Five-block | 49 | 348 | **7.102** |
| Six-block | 232 | 348 | **1.500** |

---

## Notes

- No change to `modeling.py`, `config.py`, `C`, or previously reported
  performance numbers.
- Outer training N for the preprocessor fit in section 1 is 2,700
  (holdout seed 42).
- Inner CV train N for EPV in section 2 is 2,160 per fold.
