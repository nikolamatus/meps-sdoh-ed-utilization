# Amendment 2 — EPV diagnostic (SDOH composites)

**Date:** 2026-09-24 (UTC)
**Method:** Same as `docs/dimensionality_diagnostic.md` (outer train N=2,700 preprocessor fit; inner CV train N from `repeated_cv_metrics.csv`; EPV = mean CV train events / design columns).

| Block | Source features | Design-matrix columns |
|---|---:|---:|
| Five-block | 15 | **49** |
| SDOH composites | 7 | **7** |
| Six-block (amended) | 22 | **56** |

- Mean CV training fold size: **2160**
- Mean CV training events: **348**

| Model | EPV |
|---|---:|
| Five-block | **7.102** |
| Six-block (amended) | **6.214** |

**EPV floor (amendment Step 2):** >= 10
**Clears floor:** False

## Stop

Amended six-block EPV = 6.214 is below the floor of 10. Per `docs/pre_registration_amendment_2.md` Step 2, **do not proceed to composite-model fitting**.
