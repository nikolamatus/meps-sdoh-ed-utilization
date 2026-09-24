# Linkage feasibility memo (Task 1)

**Date:** 2026-09-23  
**Status:** Documentation-only feasibility determination. No microdata
loaded. No models trained.  
**Decision:** **YELLOW — linkage is feasible on HC-245 alone for Panel
24 adults with SDOH data; exact analytic N after the dual cohort rule
is not yet known.**

This memo answers the Task 1 questions from published AHRQ sources
only. Citations are listed at the end. Nothing here invents a join that
documentation does not support.

---

## 1. Exact PUF identifier for the 2021 SDOH / SHE instrument

**Finding:** The 2021 Social Determinants of Health (SDOH) Survey /
Social and Health Experiences (SHE) self-administered questionnaire
was **not** released as a standalone SAQ-only PUF.

| Release | PUF ID | Role for this project |
|---|---|---|
| 2021 Full Year Consolidated | **HC-233** | Original multi-panel home of SDOH items (`SDOHELIG`, `SD*` stems) and the SDOH person weight `SDOHWT21F` |
| Panel 24 4-Year Longitudinal | **HC-245** | **Primary analysis file.** Carries the same SDOH items with Round-5 suffixes (`SDOHELIG5`, `SD*5`) for Panel 24 |

**Sources:** HC-233 documentation, Social Determinants of Health Survey
section; HC-245 documentation Table 1 naming note (“The SDOH survey was
fielded during Panel 24 Round 5”); HC-245 codebook entries for
`SDOHELIG5` and related `SD*5` variables.

**Correction to the prior-thread assumption of a separate “SDOH SAQ
PUF”:** AHRQ’s published file list places these variables on HC-233
(and, for Panel 24, on HC-245). Treating “HC number unknown” as a
blocker is no longer accurate; treating a phantom separate SAQ file as
required would be incorrect.

---

## 2. Can `DUPERSID` join SDOH to the Panel 24 longitudinal cohort?

### Primary path (no join required)

For Panel 24 persons on **HC-245**, SDOH variables are **already on the
same person row** as `ERTOTY1`–`ERTOTY4` and `YEARIND`. The linkage key
is identity: one `DUPERSID`, one record. HC-245 documentation maps
consolidated names to Round-5 longitudinal names (e.g. `SDOHELIG` =
`SDOHELIG5`).

**Implication:** The companion analytic design (HC-245, `YEARIND == 1`,
valid ED counts) can be extended with SDOH predictors without merging
a second file, provided `SDOHELIG5` and the chosen `SD*5` columns are
present at runtime (fail closed if absent).

### Optional path (HC-233 ↔ HC-245)

Both files use `DUPERSID` as the person ID (HC-233 and HC-245
codebooks: “PERSON ID (DUID + PID)”). From 2018 onward, `DUPERSID`
embeds the panel number in `DUID`, so Panel 24 IDs are cross-panel
unique in the sense documented by AHRQ for post-2017 ID lengths.

A clean person-level join of Panel 24 rows between HC-245 and HC-233 is
**expected** for persons who appear on both files, but:

- HC-233 contains four panels for calendar year 2021; only Panel 24
  rows are relevant to HC-245.
- Not every HC-245 person necessarily has a usable SDOH record (see
  eligibility).
- Concordance of `SD*` (HC-233) vs `SD*5` (HC-245) values must be
  checked at runtime if both files are supplied — not assumed.

**Pipeline rule:** If HC-233 is absent, proceed with HC-245-only SDOH
columns. If HC-233 is present, join on `DUPERSID` among Panel 24
persons and fail closed if the key is missing, duplicated, or if a
required SDOH column is absent on both sides of a validation check.

---

## 3. Eligibility restrictions (confirmed, not repeated uncritically)

From **HC-233 documentation** (Social Determinants of Health Survey):

| Rule | Documented statement |
|---|---|
| Age | All adults **age 18 and older** as of the Round 1/3/5/7 interview date (`AGE31X >= 18`) were asked to complete the SDOH |
| Gate questions | **No** gate questions; all questions asked of all SDOH respondents regardless of age (within adult eligibility), sex, or health status |
| Fielding rounds | Panel 23 Round 7; **Panel 24 Round 5**; Panel 25 Round 3; Panel 26 Round 1 |
| Modes | First MEPS-HC instrument administered as **paper and web** |
| `SDOHELIG` | 0 = not eligible; 1 = eligible **and has SDOH data**; 2 = eligible but **no** SDOH data |
| Ineligibility reasons | No record in the round; not key; deceased or institutionalized; moved out of the U.S. or to a military facility; disposition inapplicable; **age < 18** |
| Proxy | Paper form allowed proxy; relationship in `SDPROX` / `SDPROX5` |
| Timing | Target population described as adults at Rounds 1/3/5/7 collection (generally late winter / spring **2021**) |

From **HC-245 codebook** (`SDOHELIG5`, “ELIGIBILITY STATUS FOR SDOH 21”):

| Code | Unweighted N (full HC-245, N = 5,565) |
|---|---|
| −1 Inapplicable | 310 |
| 0 Not eligible | 1,027 |
| **1 Eligible and has SDOH data** | **3,640** |
| 2 Eligible but no SDOH data | 588 |

**Confirmed relative to the prior thread:**

- **Adults 18+:** yes (documented).
- **Single 2021 cross-section per person:** yes — one SDOH administration
  per panel (for Panel 24, Round 5 in 2021). Not a multi-year SDOH panel.
- **Children:** not SDOH-eligible; they remain in the companion
  all-age ED cohort unless this study explicitly restricts to
  `SDOHELIG5 == 1` (recommended; see §4).

**Temporal leakage:** Panel 24 Round 5 falls in calendar year 2021
(HC-233: SDOH fielded in the 2021 initial rounds of each panel;
HC-245: SDOH → suffix 5). Predictors from Round 5 are on or before the
2021-12-31 cutoff used in the companion design. Round 7 remains banned
as a predictor source because it overlaps 2021/2022.

---

## 4. Population size after dual requirement

**Requirement (planned analytic cohort):**

1. Membership in the companion rule: `YEARIND == 1` and valid
   non-sentinel `ERTOTY1`–`ERTOTY4` on HC-245.
2. SDOH completion: `SDOHELIG5 == 1` (eligible and has SDOH data).

### What public documentation already shows

| Quantity | Value | Source |
|---|---|---|
| HC-245 persons | 5,565 | HC-245 documentation |
| `YEARIND == 1` | 5,108 | HC-245 documentation (also companion analytic N under the ED-validity rule) |
| `SDOHELIG5 == 1` on full HC-245 | 3,640 | HC-245 codebook |
| Companion analytic cohort (YEARIND + valid ED) | 5,108 | Companion repo outputs / same HC-245 design rule |

### What **cannot** be determined without the file

The intersection

> `YEARIND == 1` ∩ valid `ERTOTY1`–`Y4` ∩ `SDOHELIG5 == 1`

is **not published** as a single table. Plausible upper bound:
**≤ 3,640**. Whether nearly all of the 3,640 SDOH respondents also
satisfy the four-year ED-validity rule is an empirical question.

**Once `h245.dta` is supplied, the pipeline will compute and write:**

- `n_raw`, `n_yearind`, `n_valid_ed`, `n_sdoh_elig1`
- `n_analytic_companion_rule` (YEARIND + valid ED)
- `n_analytic_sdoh` (companion rule ∩ `SDOHELIG5 == 1`)
- Join report if `h233.dta` is also present (match rate, Panel 24
  subset size, concordance on overlapping `SD*` / `SD*5` items)
- Outcome event count and prevalence on the SDOH-restricted cohort

**No fabricated N, event count, or prevalence appears in this memo.**

### Scope implication (honest)

Requiring SDOH completion **restricts the sample to adults with a 2021
SDOH record** and drops children and non-respondents who remain in the
companion all-age cohort. That is a deliberate scope change, not a
silent filter. If `n_analytic_sdoh` later clears the pre-registered
decision-gate floors, the study proceeds on that adult SDOH cohort;
if not, the gate returns YELLOW/RED with the computed numbers — not an
architecture excuse.

---

## 5. Candidate SDOH variable list (feature-audit treatment)

Naming below is the **HC-245 Round-5 form** used for modeling
(`…5`). HC-233 equivalents drop the trailing `5` (except truncated
names — see note). Status **confirmed** means the name appears in the
HC-245 and/or HC-233 codebook/crosswalk. Treatment is categorical
unless noted. All have `availability_year = 2021` (Round 5 / 2021
fielding).

**Note on truncation:** HC-245 lists `SDPROBSMKDE5` (smoke detector);
HC-233 lists `SDPROBSMKDET`. Runtime must use the name present on the
loaded file; do not guess an alternate spelling.

### 5.1 Inclusion / admin (not predictors)

| Variable | Domain | Status | Treatment | Role |
|---|---|---|---|---|
| `SDOHELIG5` | Eligibility | confirmed | categorical | Cohort filter (`== 1`); never a model feature |
| `SDCMPM5`, `SDCMPY5` | Admin | confirmed | — | Completion date; not a predictor |
| `SDPROX5` | Admin | confirmed | categorical | Proxy flag; report missingness / sensitivity only |

### 5.2 Housing affordability and quality — **primary SDOH block candidates**

| Variable | Description (codebook) | Status | Treatment | Notes |
|---|---|---|---|---|
| `SDAFRDHOME5` | Affordable housing | confirmed | categorical | Include |
| `SDHOME5` | Satisfied with home | confirmed | categorical | Include |
| `SDLATERENT5` | 12 mo pay rent/mortgage late | confirmed | categorical | Include |
| `SDLATEUTIL5` | 12 mo pay utility late | confirmed | categorical | Include |
| `SDSHUTUTIL5` | 12 mo threat utility off | confirmed | categorical | Include |
| `SDPROBPEST5` | Home problem: pests | confirmed | categorical | Include |
| `SDPROBMOLD5` | Home problem: mold | confirmed | categorical | Include |
| `SDPROBLEAD5` | Home problem: lead | confirmed | categorical | Include |
| `SDPROBHEAT5` | Home problem: heat | confirmed | categorical | Include |
| `SDPROBCOOK5` | Home problem: cook | confirmed | categorical | Include |
| `SDPROBSMKDE5` | Home problem: smoke detector | confirmed | categorical | Include (HC-245 spelling) |
| `SDPROBLEAKS5` | Home problem: water leaks | confirmed | categorical | Include |
| `SDPROBNONE5` | No home problems | confirmed | categorical | Include; mutually informative with problem flags |

### 5.3 Food security — **primary**

| Variable | Description | Status | Treatment | Notes |
|---|---|---|---|---|
| `SDWRRYFD5` | 12 mo worried about food | confirmed | categorical | Include |
| `SDNOFOOD5` | 12 mo food ran out | confirmed | categorical | Include |
| `SDHLTHFOOD5` | Places for healthy food | confirmed | categorical | Neighborhood food access; include |

### 5.4 Transportation — **primary**

| Variable | Description | Status | Treatment | Notes |
|---|---|---|---|---|
| `SDNOTRANS5` | 12 mo no transport for daily needs | confirmed | categorical | Include |
| `SDPUBTRANS5` | Access to public transportation | confirmed | categorical | Include |

### 5.5 Financial strain — **primary**

| Variable | Description | Status | Treatment | Notes |
|---|---|---|---|---|
| `SDPAYBASICS5` | How hard to pay for basics | confirmed | categorical | Include |
| `SDUNEXPEXP5` | Cover unexpected expense | confirmed | categorical | Include |
| `SDMISSCCLN5` | 12 mo miss card/loan payment | confirmed | categorical | Include |
| `SDDEBT5` | 12 mo contact by collection | confirmed | categorical | Include |

### 5.6 Social support / loneliness — **primary**

| Variable | Description | Status | Treatment | Notes |
|---|---|---|---|---|
| `SDFAMILY5` | Help from family | confirmed | categorical | Include |
| `SDFRIENDS5` | Help from friends | confirmed | categorical | Include |
| `SDCOMM5` | Help from community | confirmed | categorical | Include |
| `SDTLKPHN5` | Telephone others per week | confirmed | categorical | Include |
| `SDGETTGT5` | See others per week | confirmed | categorical | Include |
| `SDCHURCH5` | Attend church/services | confirmed | categorical | Include |
| `SDCLUBORG5` | Club/org meetings per year | confirmed | categorical | Include |
| `SDCOMPAN5` | Feel lack companionship | confirmed | categorical | Include |
| `SDLEFTOUT5` | Feel left out | confirmed | categorical | Include |
| `SDISOL5` | Feel isolated | confirmed | categorical | Include |

### 5.7 Personal safety (neighborhood + interpersonal) — **primary**

| Variable | Description | Status | Treatment | Notes |
|---|---|---|---|---|
| `SDSFCRIME5` | Safe from crime/violence | confirmed | categorical | Include |
| `SDPHYSHURT5` | How often hurt by others | confirmed | categorical | Include |
| `SDINSULT5` | How often insulted | confirmed | categorical | Include |
| `SDTHRHARM5` | How often threatened harm | confirmed | categorical | Include |
| `SDSCREAM5` | How often scream/curse | confirmed | categorical | Include |

### 5.8 Adverse childhood experiences (ACEs) — **primary SDOH block**

Retrospective items about experiences before age 18. Temporally prior
to the 2021 cutoff; confirmed on HC-245.

| Variable | Description | Status | Treatment | Notes |
|---|---|---|---|---|
| `SDHMDEPR5` | Lived with mental illness <18 | confirmed | categorical | Include |
| `SDHMALC5` | Lived with alcoholic <18 | confirmed | categorical | Include |
| `SDHMDRG5` | Lived with drugs <18 | confirmed | categorical | Include |
| `SDHMJAIL5` | Lived with sentenced person <18 | confirmed | categorical | Include |
| `SDHMDIV5` | Lived with split home <18 | confirmed | categorical | Include |
| `SDHMBEAT5` | How often abused <18 | confirmed | categorical | Include |
| `SDHURTCHLD5` | How often child hurt | confirmed | categorical | Include |
| `SDINSCHLD5` | How often child insult | confirmed | categorical | Include |
| `SDTCHCHLD5` | How often child touched | confirmed | categorical | Include |
| `SDTCHADLT5` | How often asked to touch | confirmed | categorical | Include |
| `SDFRCSXCH5` | How often forced | confirmed | categorical | Include |

### 5.9 Confirmed on file but **excluded from the primary SDOH block**

| Variable | Description | Reason for exclusion |
|---|---|---|
| `SDLIFE5` | Satisfied with life | Global well-being; overlaps health-status constructs; not in the six SDOH domains named in the research question |
| `SDMEDCARE5` | Places for medical care | Neighborhood care access; overlaps the existing **access** block (`HAVEUS6` / insurance) — exclude from SDOH block to avoid double-counting the research contrast |
| `SDPARKS5` | Places for parks/play | Amenities; outside locked SDOH domains |
| `SDDAYEXER5`, `SDMINSEXER5` | Moderate exercise | Health behavior, not SDOH domain in the research question |
| `SDSTRESS5` | How often stress | Psychological distress; overlaps mental-health block |
| `SDENICPROD5` | Electronic nicotine | Substance behavior; not SDOH domain here |
| `SDDSCRMDR5` … `SDDSCRMSTR5` | Discrimination (7 items) | Documented on the SHE; conceptually adjacent but listed separately from the six domains in the research question. Reserved for a **pre-registered sensitivity** only if Task 1 gate clears — not in the primary SDOH block at lock |

Hypothesized / undocumented names are **not** used.

---

## 6. Feasibility verdict

| Question | Verdict |
|---|---|
| Is there a documented SDOH PUF? | **Yes — content on HC-233; Panel 24 copies on HC-245.** No separate SAQ-only PUF. |
| Can it attach to the Panel 24 longitudinal cohort? | **Yes.** Primary path: columns already on HC-245. Optional: `DUPERSID` join to HC-233. |
| Eligibility constraint? | **Adults 18+, one 2021 administration; use `SDOHELIG5 == 1`.** |
| Exact dual-cohort N? | **Unknown until `h245.dta` is loaded.** Upper bound ≤ 3,640 from the public codebook. |
| Proceed to Task 2 / scaffold modeling code? | **Yes — with the YELLOW caveat that GREEN/YELLOW/RED for predictive feasibility waits on real N, events, and lifts.** |

This memo does **not** authorize fitting models on real data, inventing
placeholder metrics, or claiming national representativeness.

---

## Sources consulted (AHRQ / MEPS)

1. MEPS HC-233: 2021 Full Year Consolidated Data File documentation  
   https://meps.ahrq.gov/data_stats/download_data/pufs/h233/h233doc.shtml  
   (Social Determinants of Health Survey section; `SDOHELIG`;
   `SDOHWT21F` weighting section stating 18,400 persons with SDOH
   weight; Variable-Source Crosswalk of `SD*` items.)
2. MEPS HC-233 codebook (`DUPERSID`, `SDOHWT21F`, `SDOHELIG`)  
   https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_codebook.jsp?PUFId=H233
3. MEPS HC-245: Panel 24, 4-Year Longitudinal Public Use File
   documentation  
   https://meps.ahrq.gov/data_stats/download_data/pufs/h245/h245doc.shtml  
   (Table 1 SDOH5 naming; note that SDOH was fielded in Round 5;
   `YEARIND` frequencies.)
4. MEPS HC-245 codebook (`SDOHELIG5` frequencies; `SD*5` variable list)  
   https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_codebook.jsp?PUFId=H245  
   https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_codebook.jsp?PUFId=H245&varName=SDOHELIG5
5. MEPS HC-245 / HC-233 public download detail pages (PUF numbers and
   release labels).
