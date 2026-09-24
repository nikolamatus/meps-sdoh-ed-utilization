# Data sources

This project uses AHRQ MEPS Household Component public-use files.
Variable names and file IDs below are taken from published AHRQ
documentation and codebooks cited in each section. Runtime ingest still
requires the listed columns to exist on the loaded file(s). Unknown
availability fails closed.

**No microdata have been loaded in this repository yet.** Counts cited
from public codebooks are documentation facts, not pipeline outputs.

---

## Primary file (required)

**AHRQ Medical Expenditure Panel Survey (MEPS), Household Component**

| Field | Value |
|---|---|
| **PUF ID** | **HC-245** |
| **Title** | Panel 24, 4-Year Longitudinal Public Use File |
| **Coverage** | Calendar years 2019–2022 (Rounds 1–9) |
| **Documentation** | https://meps.ahrq.gov/data_stats/download_data/pufs/h245/h245doc.shtml |
| **Codebook** | https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_codebook.jsp?PUFId=H245 |
| **Download page** | https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_detail.jsp?cboPufNumber=HC-245 |
| **Expected local path** | `data/raw/h245.dta` (Stata release) |
| **Person identifier** | `DUPERSID` (DUID + PID; one row per person) |

HC-245 documentation states the file contains 5,565 persons and 5,321
variables. The same documentation’s Table 1 naming conventions map
full-year consolidated SDOH item names onto longitudinal Round-5 names
(example: `SDOHELIG` → `SDOHELIG5`, `SDAFRDHOME` → `SDAFRDHOME5`) because
the SDOH survey was fielded in Panel 24 Round 5.

The pipeline does **not** download from AHRQ. `feasibility/download.py`
locates a user-supplied `.dta` in `data/raw/` and records file size and
SHA-256 in `data/raw/provenance.json`. If the file is absent, it prints
manual-placement instructions and exits non-zero.

---

## 2021 SDOH / SHE instrument — where the variables live

**There is no separate AHRQ public-use file whose sole content is the
2021 SDOH Self-Administered Questionnaire.** That conclusion is from
AHRQ’s own file inventory and documentation, not an inference from
silence.

The 2021 Social Determinants of Health Survey (also described as the
Social and Health Experiences / SHE self-administered questionnaire)
was released as constructed variables on:

### A. HC-233 — 2021 Full Year Consolidated Data File

| Field | Value |
|---|---|
| **PUF ID** | **HC-233** |
| **Title** | 2021 Full Year Consolidated Data File |
| **Documentation** | https://meps.ahrq.gov/data_stats/download_data/pufs/h233/h233doc.shtml |
| **Codebook** | https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_codebook.jsp?PUFId=H233 |
| **Download page** | https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_detail.jsp?cboPufNumber=HC-233 |
| **SDOH weight** | `SDOHWT21F` (person-level SDOH weight; HC-233 codebook) |
| **Eligibility** | `SDOHELIG` |
| **Item prefix** | Variables created from the SDOH begin with `SD` (HC-233 documentation, Social Determinants of Health Survey section) |

HC-233 documentation (section on the Social Determinants of Health
Survey) states:

- The SDOH includes questions on housing, financial well-being, food
  security, social support, discrimination, and physical and sexual
  violence.
- It was fielded during Panel 23 Round 7, Panel 24 Round 5, Panel 25
  Round 3, and Panel 26 Round 1.
- All adults age 18 and older as of the Round 1/3/5/7 interview date
  (`AGE31X >= 18`) were asked to complete it.
- `SDOHELIG` = 0 (not eligible), 1 (eligible and has SDOH data), or 2
  (eligible but no SDOH data).
- 18,400 persons were assigned a positive `SDOHWT21F` (pooled panels).

### B. HC-245 — same SDOH items, Panel 24 Round-5 suffixes (primary path)

Because this study’s longitudinal cohort is Panel 24 HC-245, the
**primary** SDOH source for modeling is the Round-5-suffixed copies
already present on HC-245 (confirmed in the HC-245 HTML codebook, e.g.
`SDOHELIG5`, `SDAFRDHOME5`). A separate join to HC-233 is **not
required** to obtain SDOH predictors for Panel 24 persons who are on
HC-245.

### C. Optional second file (validation / weights only)

| Role | File | When used |
|---|---|---|
| Required | `h245.dta` | Always |
| Optional | `h233.dta` | If supplied: join on `DUPERSID` to cross-check Panel-24 SDOH values and to record `SDOHWT21F`. Not required for the unweighted predictive design. |

If only HC-245 is present, the ingest layer proceeds. If HC-233 is
present, `feasibility/linkage.py` reports join rates and value
concordance and fails closed on a broken key.

---

## Core longitudinal design variables (HC-245)

Same roles as the companion ED-utilization study:

| Variable | Role |
|---|---|
| `DUPERSID` | Person ID; must be unique |
| `ERTOTY1`–`ERTOTY3` | ED visit counts 2019–2021 (predictors) |
| `ERTOTY4` | ED visit counts 2022 (**outcome only**) |
| `YEARIND` | Cohort inclusion; `YEARIND == 1` = in file for all four years 2019–2022 (HC-245 documentation §2.1.2) |
| `ALL9RDS` | Reported, not required for analytic cohort |
| `LONGWT`, `VARSTR`, `VARPSU` | Recorded, not applied to sklearn metrics |
| `SDOHELIG5` | SDOH eligibility / response flag (Round 5 / 2021) |

---

## Baseline (non-SDOH) predictors

Confirmed HC-245 names, identical to the companion lock set:

| Family | Variables |
|---|---|
| Demographics | `AGEY3X`, `SEX`, `RACETHX`, `REGIONY3`, `MARRY6X` |
| Health status | `RTHLTH6`, `MNHLTH6` |
| Access | `INSCOVY3`, `HAVEUS6` |
| Socioeconomic | `POVCATY3`, `TTLPY3X`, `EMPST6` |
| Prior utilization | `ERTOTY1`, `ERTOTY2`, `ERTOTY3` |

Post-cutoff counterparts (`AGEY4X`, `INSCOVY4`, Round 8–9 names, etc.)
remain banned. Round 7 overlaps 2021/2022 and is not used as a
predictor.

---

## Manual placement instructions

1. Open the HC-245 download page linked above.
2. Download the Stata-format Data File (`.zip`).
3. Unzip and place the `.dta` at `data/raw/h245.dta`.
4. Optionally download HC-233 Stata `.dta` to `data/raw/h233.dta` for
   linkage validation and SDOH-weight provenance.
5. Re-run `python -m feasibility.download` (or the full pipeline).

Do not substitute a two-year longitudinal file for HC-245.

---

## AHRQ public-use constraints

HC-245 and HC-233 are distributed by AHRQ as public-use files. Users
must obtain them from AHRQ and follow AHRQ public-use conditions. This
repository does not redistribute the microdata. Do not attempt to
identify individuals.

AHRQ requests that users cite AHRQ and the Medical Expenditure Panel
Survey as the data source in publications based on these data.
