# Limitations

These limitations apply to the completed dual-cohort analysis
(N = 3,601; gate **YELLOW**). State them whenever results are described.

This study **demonstrates** unweighted predictive discrimination on a
MEPS Panel 24 **adult SDOH-respondent** analytic sample under a locked
design. It **does not** establish that SDOH adds incremental value in
that sample under the pre-registered six-block specification. It
**leaves unknown** whether a different, prospectively locked SDOH subset,
another panel, or weighted estimation would change that conclusion.

---

## 1. SDOH eligibility and adult-only scope

SDOH / SHE was fielded to adults 18+ with a single 2021 administration.
Requiring `SDOHELIG5 == 1` drops children and SDOH non-respondents who
remain in the companion all-age cohort (5,108 → 3,601). Findings do not
transport to pediatric ED prediction.

## 2. Single cross-section SDOH

SDOH predictors are one 2021 snapshot (Panel 24 Round 5), not a
multi-year SDOH panel. Change in social risk over 2019–2021 is unmeasured.

## 3. Self-report and proxy response

SHE items are self-administered (paper/web); proxy completion is possible
(`SDPROX5`). Measurement error can attenuate predictive associations.

## 4. Large sparse SDOH block

The locked primary SDOH block includes 48 categorical items. With N ≈
2,700 training persons and L2 logistic regression at fixed `C=1.0`, the
block can add noise relative to a tighter specification. This run does
**not** authorize post-hoc item hunting; any reduced SDOH set would need
a dated pre-registration amendment **before** fitting.

## 5. Unweighted metrics

ROC-AUC, PR-AUC, and Brier are unweighted person-level scores on the
analytic sample. `LONGWT` / `SDOHWT21F` were recorded for provenance and
not applied. Results are not national MEPS estimates.

## 6. Public-use MEPS coverage

MEPS-HC covers the U.S. civilian noninstitutionalized population. It
excludes incarcerated, active-duty military, and institutionalized
populations and undersamples people experiencing homelessness. Panel 24
overlaps COVID-19; AHRQ documents related data-quality concerns.

## 7. Single-panel, no external validation

All modeling uses Panel 24 only. The 25% holdout is first-run internal
evaluation, not an independent population or later panel.

## 8. Model class and fixed hyperparameters

L2-regularized logistic regression with fixed `C=1.0`. No post-lock
hyperparameter search. Incremental discrimination is specific to this
estimator and the locked feature set.

## 9. Imputation

Negatives → missing; single median/mode imputation inside training
folds. Not multiple imputation.

## 10. No causal or clinical claims

No causal interpretation of coefficients, no clinical utility, no
“avoidable/preventable” ED use, and no deployment readiness are
supported by this analysis.

## 11. Gate YELLOW is not a soft GREEN

The pre-registered incremental ROC lift for the **six-block** full model
vs ED-history failed on the locked holdout (Δ ROC = −0.002; need ≥
0.02). Continuity evidence that the five-block model looks better than
ED-history on this adult subset does **not** rescue the SDOH-extension
gate, because the registered full model includes SDOH and SDOH’s
marginal contribution was negative.
