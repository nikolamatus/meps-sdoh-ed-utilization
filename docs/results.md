# Results

**Analysis date:** 2026-09-23 (local) / 2026-09-24 UTC run stamps  
**Pre-registration:** `docs/pre_registration.md` (2026-09-23)  
**Decision gate:** **YELLOW**

This file reports computed numbers only. It does not invent statistics.

---

## Stage reached

All stages completed through Stage 4. No stage gate stopped the run:

| Stage | Result |
|---|---|
| 0 Provenance | Both files loaded; schema OK |
| 1 Dual cohort / Gate 1 | **PASS** (N = 3,601 ≥ 1,500) |
| 2 Feature audit / Gate 2 | **PASS** (injection of `ERTOTY4` / `AGEY4X` caught) |
| 3 Modeling + inference | Completed |
| 4 Decision gate | **YELLOW** |

---

## Dual-cohort N (most important design number)

| Quantity | Value | Check |
|---|---:|---|
| HC-245 persons | 5,565 | matches documentation |
| Companion cohort (`YEARIND==1` ∧ valid ED) | **5,108** | matches companion / expected |
| `SDOHELIG5==1` (full HC-245) | **3,640** | matches codebook |
| **Dual cohort** (companion ∧ `SDOHELIG5==1`) | **3,601** | — |
| Dual-cohort events (`ERTOTY4≥1`) | **580** | — |
| Dual-cohort prevalence | **0.1611** | — |
| Train / holdout (seed 42) | 2,700 / 901 | — |

HC-233 Panel-24 `DUPERSID` match rate vs HC-245: 0.9447. All 48 primary
SDOH item values agreed exactly on overlapping non-missing cells. HC-245
remained the analysis file.

---

## Locked holdout (first-run internal evaluation — not external validation)

| Model | ROC-AUC | PR-AUC | Brier |
|---|---:|---:|---:|
| ED-history (`ERTOTY1`–`Y3`) | 0.6584 | 0.3421 | 0.1218 |
| Five-block (no SDOH) | 0.6799 | 0.3849 | 0.1209 |
| Six-block full (+ SDOH) | 0.6560 | 0.3561 | 0.1282 |

| Holdout contrast | Δ ROC | Δ PR |
|---|---:|---:|
| Six − ED (gate input) | **−0.0024** | +0.0140 |
| Five − ED | +0.0215 | +0.0427 |
| Six − Five (SDOH marginal) | **−0.0240** | −0.0287 |

---

## Training-only 5×5 repeated CV (mean over 25 folds)

| Model | ROC-AUC | PR-AUC | Brier |
|---|---:|---:|---:|
| ED-history | 0.7106 | 0.3647 | 0.1217 |
| Five-block | 0.7336 | 0.3982 | 0.1195 |
| Six-block | 0.7019 | 0.3607 | 0.1272 |

---

## Inferential contrasts (Nadeau–Bengio, df = 24)

Continuity contrasts were requested in the analysis prompt in addition to
the pre-registered Family A/B set. Pre-registration remains authoritative
for which hypotheses are primary vs secondary (see conflict note below).

### Continuity + Family A

| ID | Contrast | Metric | Mean Δ | Corrected SE | t | raw p | Holm |
|---|---|---|---:|---:|---:|---:|---|
| C_five_vs_ed | Five − ED | ROC | +0.0230 | 0.0125 | +1.831 | 0.0795 | — |
| C_five_vs_ed | Five − ED | PR | +0.0335 | 0.0144 | +2.334 | 0.0283 | — |
| C_five_vs_ed | Five − ED | Brier | −0.0022 | 0.0014 | −1.521 | 0.1413 | — |
| C_six_vs_five | Six − Five (SDOH) | ROC | **−0.0316** | 0.0111 | −2.845 | **0.0089** | — |
| C_six_vs_five | Six − Five (SDOH) | PR | **−0.0375** | 0.0174 | −2.158 | **0.0412** | — |
| C_six_vs_five | Six − Five (SDOH) | Brier | **+0.0077** | 0.0023 | +3.279 | **0.0032** | — |
| **A1** | **Six − ED** | ROC | **−0.0087** | 0.0121 | −0.715 | **0.4812** | — |
| A1 | Six − ED | PR | −0.0040 | 0.0208 | −0.192 | 0.8491 | — |
| A1 | Six − ED | Brier | +0.0055 | 0.0028 | +1.982 | 0.0591 | — |

### Family B (leave-one-block-out vs six-block full; Holm within family, per metric)

Selected ROC rows (full table: `outputs/statistical_inference.csv`):

| ID | Contrast | Mean Δ ROC | Corrected SE | raw p | Holm p |
|---|---|---:|---:|---:|---:|
| B1 | No-age − Full | −0.0069 | 0.0035 | 0.0576 | 0.2305 |
| B2 | No-demographics − Full | +0.0044 | 0.0033 | 0.2004 | 0.4720 |
| B3 | No-health − Full | +0.0013 | 0.0040 | 0.7564 | 0.7564 |
| B4 | No-access − Full | −0.0035 | 0.0016 | 0.0421 | 0.2106 |
| B5 | No-SES − Full | +0.0035 | 0.0024 | 0.1573 | 0.4720 |
| **B6** | **No-SDOH − Full** | **+0.0316** | 0.0111 | **0.0089** | **0.0536** |

B6 Brier Holm-adjusted p = **0.0190** (removing SDOH improves Brier after
Holm). B6 ROC does **not** clear α = 0.05 after Holm (0.0536).

B6 mean Δ ROC = −(Six − Five): removing the SDOH block improves
discrimination relative to the six-block full model on these folds.

---

## Decision gate (pre-registered floors)

| Floor | Threshold | Observed | Pass? |
|---|---:|---:|---|
| Usable N | ≥ 1,500 | 3,601 | yes |
| Events | ≥ 100 | 580 | yes |
| Prevalence | ≥ 0.03 | 0.161 | yes |
| Prior-ED ROC | ≥ 0.55 | 0.658 | yes |
| Full − ED ROC lift | ≥ 0.02 | **−0.002** | **no** |
| Full − ED PR lift | ≥ 0.01 | +0.014 | yes |
| SDOH family present | required | yes | yes |
| Leakage / readiness | pass | pass | yes |

**Verdict: YELLOW** — data adequacy and baseline clear; **incremental
value of the pre-registered six-block full model vs ED-history fails**
the ROC lift floor on the locked holdout. SDOH’s marginal contrast
moves performance **down**, not up.

---

## Prompt vs pre-registration conflict (flagged, not silently resolved)

The Stage-3 prompt asked for inferential emphasis on (a) five-block vs
ED, (b) six vs five, (c) six vs ED. The locked pre-registration defines:

- **Family A primary:** A1 = six-block full − ED only
- **Family B secondary:** B1–B6 leave-one-block-out vs six-block full,
  Holm within family

Continuity contrasts (a)(b) are reported here and in
`statistical_inference.csv` with `family=continuity` and **no** Holm
adjustment. They are **not** additional Family A hypotheses. Document
wins for gate and primary claim language: the gate evaluates the
**six-block** full model.

---

## What this run establishes

- The dual cohort is large enough to run the locked design (N = 3,601;
  580 events).
- On this adult SDOH-respondent sample, the **five-block** companion-style
  model shows a positive descriptive lift over ED-history.
- Adding the **locked 48-item SDOH block** does **not** improve
  discrimination; CV and holdout both show worse ROC/PR/Brier for
  six-block vs five-block.
- Primary A1 (six − ED) is not detectably positive under Nadeau–Bengio.

## What this run does not establish

- No causal effect of SDOH on ED use
- No clinical utility or “preventable ED” claim
- No nationally representative (survey-weighted) performance
- No claim that *no* SDOH subset could help — only that the
  **pre-registered full SDOH block** does not
- No external or later-panel validation
