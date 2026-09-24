# Limitations

These limitations apply regardless of any future decision-gate status.
State them whenever results from this repository are described.

This study, once run on real files, will **demonstrate** unweighted
predictive discrimination on a MEPS Panel 24 **adult SDOH-respondent**
analytic sample. It will **not** establish causality, clinical utility,
avoidability of ED visits, or nationally representative performance.

---

## 1. SDOH eligibility and adult-only scope

SDOH / SHE was fielded to adults 18+ with a single 2021 administration.
Requiring `SDOHELIG5 == 1` drops children and SDOH non-respondents who
remain in the companion all-age cohort. Findings do not transport to
pediatric ED prediction.

## 2. Single cross-section SDOH

SDOH predictors are one 2021 snapshot (Panel 24 Round 5), not a
multi-year SDOH panel. Change in social risk over 2019–2021 is unmeasured.

## 3. Optional HC-233 join

Primary analysis uses HC-245 `SD*5` columns. If HC-233 is absent,
`SDOHWT21F` is unavailable; the design already does not apply survey
weights to sklearn metrics.

## 4. Unweighted metrics

ROC-AUC, PR-AUC, and Brier are unweighted person-level scores on the
analytic sample, not survey-weighted national estimates.

## 5. Public-use MEPS coverage

MEPS-HC covers the U.S. civilian noninstitutionalized population. It
excludes incarcerated, active-duty military, and institutionalized
populations and undersamples people experiencing homelessness. Panel 24
overlaps COVID-19; AHRQ documents related data-quality concerns.

## 6. Single-panel, no external validation

All planned modeling uses Panel 24 only. No claims file, EHR extract,
or later MEPS panel is used as an external or temporal test set.

## 7. Model class and fixed hyperparameters

L2-regularized logistic regression with fixed `C=1.0`. No post-lock
hyperparameter search. Incremental discrimination is specific to this
estimator.

## 8. Imputation

Negatives → missing; single median/mode imputation inside training
folds. Not multiple imputation.

## 9. Discrimination battery and other SHE items

Discrimination, exercise, stress, e-nicotine, life satisfaction, and
`SDMEDCARE5` / `SDPARKS5` are excluded from the primary SDOH block by
pre-registration. That is a design choice, not evidence those domains
lack association with ED use.

## 10. No fabricated results

Until user-supplied files are analyzed, this repository contains **no
empirical performance numbers**. Do not treat documentation codebook
frequencies (e.g. 3,640 SDOH-positive persons on HC-245) as pipeline
outputs for the dual analytic cohort.
