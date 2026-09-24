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

**Dual-cohort analysis complete — decision gate YELLOW.** See
`docs/results.md`. Raw MEPS files stay local under `data/raw/` and are
not redistributed.

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
| `docs/results.md` | Computed dual-cohort results and gate |
| `docs/limitations.md` | Scope and interpretation limits |

## Citation

Cite AHRQ and the Medical Expenditure Panel Survey as the data source
for any work based on these files.
