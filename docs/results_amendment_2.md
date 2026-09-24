# Results — Amendment 2 (SDOH composites)

**Date:** 2026-09-24  
**Status:** **STOPPED at Step 2 (EPV gate). No composite model was fit.**

---

## What was completed

| Step | Result |
|---|---|
| 1. Composite pre-registration | Written: `docs/pre_registration_amendment_2.md` (seven domain hardship counts; higher = more hardship; Health Affairs MEPS SHE / ACE-count precedent) |
| 2. Re-derive EPV | **FAIL floor** — see `docs/epv_amendment_2.md` |
| 3. Lock amendment for modeling | **Not reached** |
| 4. Single Stage-3 rerun | **Not run** |

---

## Step 2 numbers (same method as dimensionality diagnostic)

| Quantity | Value |
|---|---:|
| Five-block design columns | 49 |
| SDOH composite design columns | 7 |
| Amended six-block design columns | 56 |
| Mean CV training fold size | 2,160 |
| Mean CV training events | 348 |
| Five-block EPV | 7.102 |
| **Amended six-block EPV** | **6.214** |
| Pre-registered EPV floor | ≥ 10 |

**Gate:** 6.214 < 10 → stop.

---

## Why Step 4 was not run

`docs/pre_registration_amendment_2.md` required proceeding to the single
CV / Nadeau–Bengio / Holm rerun **only if** amended six-block EPV ≥ 10.
The floor was not met. Fitting anyway would violate the amendment.

No Six-vs-Five or Five-vs-ED composite-model contrasts exist for this
amendment, because no composite model was trained.

---

## What this does not do

- Does not reopen or “pick” against the superseded 48-item run
- Does not retune `C` or redefine composites after seeing EPV
- Does not claim that a different composite scheme would clear EPV;
  that would need a new dated amendment before any further work

---

## Final conclusion — underpowered / inconclusive

Neither the raw 48-item SDOH block (**EPV 1.500**, six-block design
width 232) nor the seven-domain composite block (**EPV 6.214**, six-block
design width 56) could be evaluated at adequate power on this dual cohort
(**N = 3,601**, **580** outcome events; mean CV training events = 348).

The five-block baseline itself sits at **EPV 7.102** (49 design columns),
which is already below the pre-registered floor of **10**. The limitation
is therefore **not specific to SDOH encoding**; it is a **sample-size /
events-per-variable ceiling that predates SDOH’s addition**.

**Conclusion:** This cohort cannot support a well-powered test of whether
SDOH adds predictive value beyond the existing five-block model, at any
tested level of SDOH dimensionality. The research question **remains
open**. It is **not** answered negatively.

The original Six-vs-Five negative finding from the raw 48-item run is
**superseded** and **must not** be read as evidence that SDOH is
unhelpful. Per the dimensionality diagnostic
(`docs/dimensionality_diagnostic.md`), that pattern is evidence of
**overparameterization**, not of a substantive null for SDOH.

This project does **not** carry a GREEN / YELLOW / RED decision-gate
label for the SDOH-extension question after amendment 2: those labels
apply to a completed gate on an adequately powered specification, which
this repository did not reach.
