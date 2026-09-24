# meps-sdoh-ed-utilization

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
| `docs/pre_registration_amendment_2.md` | SDOH composite measurement lock |
| `docs/limitations.md` | Scope and interpretation limits |

## Citation

Cite AHRQ and the Medical Expenditure Panel Survey as the data source
for any work based on these files.
