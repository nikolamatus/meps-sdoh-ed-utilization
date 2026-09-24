# Limitations

These limitations apply to work in this repository on the MEPS Panel 24
SDOH-restricted dual cohort (N = 3,601; 580 events). State them whenever
results or status are described.

**Project status after amendment 2:** inconclusive — underpowered (see
`docs/results_amendment_2.md`). The research question whether SDOH adds
predictive value beyond the five-block model **remains open**. An early
YELLOW call on the raw 48-item six-block specification is **superseded**
as a substantive SDOH conclusion (overparameterization, not a well-powered
null).

---

## 1. Sample size / EPV ceiling

Named separately from adult-only eligibility and from causal /
representativeness limits.

On the dual cohort, mean CV training events are **348**. Design-matrix
widths and events-per-variable (EPV = 348 / columns), same method as
`docs/dimensionality_diagnostic.md` and `docs/epv_amendment_2.md`:

| Specification | Design columns | EPV |
|---|---:|---:|
| Five-block (no SDOH) | 49 | 7.102 |
| Six-block, 7 SDOH composites | 56 | 6.214 |
| Six-block, 48 raw SDOH items | 232 | 1.500 |

The pre-registered amendment-2 floor was EPV ≥ 10. **None** of these
specifications clear it — including the five-block model without SDOH.
That is a cohort events ceiling, not an artifact of one SDOH encoding.

**Arithmetic only (not a recommendation to re-run):** at the amended
six-block width of **56** columns, EPV 10 requires
\(10 \times 56 = 560\) training-fold events. Clearing EPV 10 with fewer
columns would require proportionally fewer events (e.g. 40 columns → 400
events). This repository does not treat those figures as a mandate to
collect or pool more data.

## 2. SDOH eligibility and adult-only scope

SDOH / SHE was fielded to adults 18+ with a single 2021 administration.
Requiring `SDOHELIG5 == 1` drops children and SDOH non-respondents who
remain in the companion all-age cohort (5,108 → 3,601). Findings do not
transport to pediatric ED prediction.

## 3. Single cross-section SDOH

SDOH predictors are one 2021 snapshot (Panel 24 Round 5), not a
multi-year SDOH panel. Change in social risk over 2019–2021 is unmeasured.

## 4. Self-report and proxy response

SHE items are self-administered (paper/web); proxy completion is possible
(`SDPROX5`). Measurement error can attenuate predictive associations.

## 5. SDOH dimensionality / overparameterization (historical raw block)

The original primary SDOH block used 48 categorical items (232
design-matrix columns after one-hot). That specification is superseded
for substantive inference. Composite reduction (7 domain counts) improved
EPV but still did not clear the floor of 10.

## 6. Unweighted metrics

Where models were fit, ROC-AUC, PR-AUC, and Brier are unweighted
person-level scores on the analytic sample. `LONGWT` / `SDOHWT21F` were
recorded for provenance and not applied. Results are not national MEPS
estimates.

## 7. Public-use MEPS coverage

MEPS-HC covers the U.S. civilian noninstitutionalized population. It
excludes incarcerated, active-duty military, and institutionalized
populations and undersamples people experiencing homelessness. Panel 24
overlaps COVID-19; AHRQ documents related data-quality concerns.

## 8. Single-panel, no external validation

Analyses use Panel 24 only. A 25% holdout is first-run internal
evaluation, not an independent population or later panel.

## 9. Model class and fixed hyperparameters

Where fit: L2-regularized logistic regression with fixed `C=1.0`. No
post-lock hyperparameter search.

## 10. Imputation

Negatives → missing; single median/mode imputation inside training
folds. Not multiple imputation. Ambiguous SDOH collapse codes are
treated as missing in amendment-2 composites.

## 11. No causal or clinical claims

No causal interpretation of coefficients, no clinical utility, no
“avoidable/preventable” ED use, and no deployment readiness are
supported by this analysis.

## 12. Superseded raw-item Six-vs-Five contrast

The raw 48-item Six-vs-Five negative heldout/CV pattern must **not** be
cited as evidence that SDOH is unhelpful. It is evidence of
overparameterization relative to available events. The question whether
SDOH adds value on this design remains **unanswered** at adequate power.
