# Social Determinants of Health and Emergency Department Utilization: A Pre-Registered Feasibility Study

Predictive feasibility study: does the 2021 MEPS Social Determinants of
Health (SDOH) / Social and Health Experiences (SHE) instrument add
discrimination for 2022 emergency department use beyond the
demographic, health-status, access, socioeconomic, and ED-history
blocks already validated on MEPS Panel 24?

This repository reuses the leakage-safe, training-only repeated-CV
design of the companion `ed-utilization-model` project and adds SDOH
as a sixth predictor block. It does **not** redistribute AHRQ microdata.

## Status

**Inconclusive — underpowered.** See `docs/results_amendment_2.md` and
`docs/limitations.md`. Raw MEPS files stay local under `data/raw/` and
are not redistributed.

This project does **not** carry a GREEN / YELLOW / RED decision-gate
label after amendment 2: those labels require a completed gate on an
adequately powered specification.

## Future Work / Reopening This Question

This project could not determine whether SDOH adds predictive value
beyond the five-block model, because of a sample-size / EPV ceiling on
the dual cohort. See `docs/limitations.md` (section on sample size /
EPV ceiling) for the arithmetic already recorded there on what training
event count would clear EPV 10 at the amended column width — not
re-derived here.

Two concrete paths to reopen the question later:

1. A future MEPS panel with a larger SDOH-eligible analytic cohort.
2. Pooling multiple panels’ SDOH / SHE waves **if** AHRQ releases them,
   once that is confirmed against actual future AHRQ documentation (not
   guessed).

## Quick start (after data are placed)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
pytest
python -m feasibility.run       # fails closed if data/raw is empty
```

## Documentation

| Document | Purpose |
|---|---|
| `docs/data_sources.md` | PUF IDs, file names, provenance rules |
| `docs/linkage_feasibility.md` | Task 1: can SDOH join the Panel 24 cohort? |
| `docs/pre_registration.md` | Locked analysis plan (before any model fit) |
| `docs/methodology.md` | Methods narrative |
| `docs/results.md` | Early dual-cohort run (superseded for SDOH inference) |
| `docs/results_amendment_2.md` | Amendment-2 stop / underpowered conclusion |
| `docs/pre_registration_amendment_2.md` | SDOH composite definitions (modeling not authorized) |
| `docs/dimensionality_diagnostic.md` | Design-matrix width and EPV (48-item block) |
| `docs/epv_amendment_2.md` | EPV after seven composites (floor fail) |
| `docs/limitations.md` | Scope and interpretation limits |

## Citation

Cite AHRQ and the Medical Expenditure Panel Survey as the data source
for any work based on these files.
