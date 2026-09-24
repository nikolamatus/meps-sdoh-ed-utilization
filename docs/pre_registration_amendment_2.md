# Pre-registration amendment 2: SDOH domain composites

**Date committed:** 2026-09-24  
**Status:** measurement definitions written; modeling **not** authorized
(Step 2 EPV gate failed — see amendment log)  
**Amends:** `docs/pre_registration.md` — SDOH predictor representation only  
**Does not amend:** cohort, outcome, cutoff, CV seeds, estimator `C`, Family A/B
contrast structure, Holm within Family B, or decision-gate floors  

This amendment replaces the **48 raw SDOH item columns** in the primary
SDOH block with **seven numeric domain composites**. It is motivated by
the dimensionality diagnostic (`docs/dimensionality_diagnostic.md`:
six-block design width 232; EPV 1.500) and is a **measurement** decision,
not a performance-driven item search.

No composite definition in this document may be revised after Step 3
(EPV clearance) / after seeing Step 4 results. If a change is needed
later, log a new dated amendment.

---

## Precedent (not ad hoc scoring)

Construction follows published practice on the **same 2021 MEPS SHE /
SDOH instrument** and classic ACE scoring:

1. **Zuvekas & Miller (Health Affairs, 2024)** — MEPS 2021 SDOH SAQ:
   dichotomize SHE items into hardship indicators (e.g. food insecurity =
   sometimes/often worried or food ran out; housing problems = fair/poor
   satisfaction or specific home problems; financial problems = late
   rent/utilities, very hard to pay basics, etc.), then aggregate; ACE
   items dichotomized then **summed** (0 / 1–3 / 4+ categories in that
   paper; the underlying score is a **count of endorsed ACEs**).
2. **Felitti et al. / BRFSS ACE score** — count of endorsed ACE
   categories (higher = more adversity).
3. **USDA-style food-security item endorsement** — affirmative responses
   on worry / food-did-not-last items (MEPS `SDWRRYFD` / `SDNOFOOD`
   codes: 1 Often, 2 Sometimes, 3 Never; hardship = 1 or 2).

This amendment uses **within-domain counts of endorsed hardship
indicators** (integer scores). That is the same logic as the ACE count,
applied domain-wise, and matches Health Affairs’ indicator construction
without introducing performance-tuned weights.

---

## Global rules

| Rule | Specification |
|---|---|
| Units | One numeric composite per domain (treatment = `numeric`) |
| Direction | **Higher = more hardship / more adversity** (stated for every domain) |
| Sentinels | Documented MEPS negatives and any other negative → not usable (same as pipeline `recode_sentinels`) |
| Ambiguous combined codes | Values such as codebook “5 SOMETIMES OR NEVER TRUE”, “8 GOOD OR FAIR”, or other multi-category collapse codes **are not usable** for endorsement (cannot map to a single hardship state). Fail closed → missing for that item |
| Missing within domain | Let \(k\) = number of domain items with a usable (non-missing after sentinel/ambiguous drop) value. If \(k \ge \lceil 0.5 \times m \rceil\) where \(m\) is the number of items in the domain, the composite = **count of endorsed items among the \(k\) usable items**. If \(k\) is below that floor, the composite is **missing** (downstream fold-wise median imputation, unchanged) |
| Raw items in X | **Excluded.** Only the seven composites enter the SDOH block |
| Domains with <2 confirmed Task-1 items | Drop domain (none apply; all seven domains have ≥2 confirmed items) |

---

## Domain definitions

All item names are HC-245 Round-5 forms (`…5`).

### 1. Housing — `SDOH_HOUSING`

**Items (m = 12):** `SDAFRDHOME5`, `SDHOME5`, `SDLATERENT5`,
`SDLATEUTIL5`, `SDSHUTUTIL5`, `SDPROBPEST5`, `SDPROBMOLD5`,
`SDPROBLEAD5`, `SDPROBHEAT5`, `SDPROBCOOK5`, `SDPROBSMKDE5`,
`SDPROBLEAKS5`  

**Excluded from this composite:** `SDPROBNONE5` (mutually informative
with problem flags; Health Affairs housing indicator used problem /
dissatisfaction items, not a separate “none” count).

**Score type:** count of endorsed hardship indicators (0 … k).  
**Direction:** higher = more housing hardship.

**Endorsement (hardship = 1):**

| Item | Endorse if usable value is… |
|---|---|
| `SDAFRDHOME5`, `SDHOME5` | 4 or 5 (Fair / Poor on Excellent–Poor scale) |
| `SDLATERENT5`, `SDLATEUTIL5`, `SDSHUTUTIL5` | 1 (Yes) |
| `SDPROB*` (seven problem flags) | 1 (Yes / problem present) |

---

### 2. Food security — `SDOH_FOOD`

**Items (m = 3):** `SDWRRYFD5`, `SDNOFOOD5`, `SDHLTHFOOD5`

**Score type:** count of endorsed indicators.  
**Direction:** higher = more food hardship / worse food access.

| Item | Endorse if… |
|---|---|
| `SDWRRYFD5`, `SDNOFOOD5` | 1 or 2 (Often / Sometimes true) — USDA / Health Affairs food-insecurity endorsement |
| `SDHLTHFOOD5` | 4 or 5 (Fair / Poor places for healthy food) |

---

### 3. Transportation — `SDOH_TRANS`

**Items (m = 2):** `SDNOTRANS5`, `SDPUBTRANS5`

**Score type:** count of endorsed indicators.  
**Direction:** higher = more transportation hardship.

| Item | Endorse if… |
|---|---|
| `SDNOTRANS5` | 1 (Yes — lack of transport kept from daily needs) |
| `SDPUBTRANS5` | 4 or 5 (Fair / Poor access to public transportation) |

---

### 4. Financial strain — `SDOH_FINANCIAL`

**Items (m = 4):** `SDPAYBASICS5`, `SDUNEXPEXP5`, `SDMISSCCLN5`, `SDDEBT5`

**Score type:** count of endorsed indicators.  
**Direction:** higher = more financial strain.

| Item | Endorse if… |
|---|---|
| `SDPAYBASICS5` | 1 (Very hard) — Health Affairs “very hard to pay for basics” |
| `SDUNEXPEXP5` | 1 or 2 (Not at all confident / Not too confident) — Health Affairs “lacking confidence” in covering an unexpected expense |
| `SDMISSCCLN5`, `SDDEBT5` | 1 (Yes) |

---

### 5. Social support / isolation — `SDOH_SOCIAL`

**Items (m = 10):** `SDFAMILY5`, `SDFRIENDS5`, `SDCOMM5`, `SDTLKPHN5`,
`SDGETTGT5`, `SDCHURCH5`, `SDCLUBORG5`, `SDCOMPAN5`, `SDLEFTOUT5`,
`SDISOL5`

**Score type:** count of endorsed social-network problem indicators
(Health Affairs listed these ten problem types).  
**Direction:** higher = more social-network hardship / isolation.

| Item group | Endorse if… |
|---|---|
| `SDFAMILY5`, `SDFRIENDS5`, `SDCOMM5` | 3 or 4 (Very little / No help) |
| `SDTLKPHN5`, `SDGETTGT5`, `SDCHURCH5`, `SDCLUBORG5` | 0 (Never / zero times in the reference period) — Health Affairs “not talking / not getting together / not attending” |
| `SDCOMPAN5` | 3 or 4 (Sometimes / Often) — Health Affairs |
| `SDLEFTOUT5`, `SDISOL5` | 4 (Often) — Health Affairs “often feeling left out / isolated” |

---

### 6. Personal safety — `SDOH_SAFETY`

**Items (m = 5):** `SDSFCRIME5`, `SDPHYSHURT5`, `SDINSULT5`,
`SDTHRHARM5`, `SDSCREAM5`

**Score type:** count of endorsed indicators.  
**Direction:** higher = more safety / violence hardship.

| Item | Endorse if… |
|---|---|
| `SDSFCRIME5` | 4 or 5 (Fair / Poor safe from crime/violence) |
| `SDPHYSHURT5`, `SDTHRHARM5` | 2, 3, 4, or 5 (Rarely … Frequently; i.e. ever vs Never) — Health Affairs |
| `SDINSULT5`, `SDSCREAM5` | 3, 4, or 5 (Sometimes / Fairly often / Frequently) — Health Affairs |

---

### 7. ACEs — `SDOH_ACE`

**Items (m = 11):** `SDHMDEPR5`, `SDHMALC5`, `SDHMDRG5`, `SDHMJAIL5`,
`SDHMDIV5`, `SDHMBEAT5`, `SDHURTCHLD5`, `SDINSCHLD5`, `SDTCHCHLD5`,
`SDTCHADLT5`, `SDFRCSXCH5`

**Score type:** **classic ACE count** (sum of dichotomous endorsements).  
**Direction:** higher = more adverse childhood experiences.

| Item type | Endorse if… |
|---|---|
| Yes/No household items (`SDHMDEPR5` … `SDHMDIV5`) | 1 (Yes) |
| Frequency abuse items (`SDHMBEAT5` … `SDFRCSXCH5`) | 2 or 3 (Once / More than once) — Health Affairs |

---

## Six-block model under this amendment

| Block | Predictors |
|---|---|
| Age / demographics / health / access / SES / ED history | Unchanged from `docs/pre_registration.md` |
| **SDOH** | `SDOH_HOUSING`, `SDOH_FOOD`, `SDOH_TRANS`, `SDOH_FINANCIAL`, `SDOH_SOCIAL`, `SDOH_SAFETY`, `SDOH_ACE` only |

Family B leave-one-block-out **B6** removes these seven composites (not
the raw items).

Contrasts and inference (unchanged procedure):

- Continuity: Five-block − ED; Six-block − Five-block; A1 Six − ED  
- Family B B1–B6 with Holm within family  
- Same seeds: holdout 42; CV `RepeatedStratifiedKFold` 5×5, `random_state=2021`

---

## Step 2 gate (EPV floor)

Before fitting, recompute design-matrix width and EPV for the amended
six-block model with the same method as
`docs/dimensionality_diagnostic.md`.

**Proceed to Step 4 only if amended six-block EPV ≥ 10.**  
If EPV < 10, **stop**; do not fit models under this amendment.

---

## What this amendment does not authorize

- Re-opening raw 48-item SDOH in the primary model  
- Performance-based reweighting of items inside a domain  
- Changing `C`, seeds, cohort, or gate floors  
- Treating this run as “winner” vs the superseded 48-item run  

---

## Amendment log

- 2026-09-24: Amendment 2 written (seven domain composites defined from
  Health Affairs MEPS SHE / ACE-count precedent).
- 2026-09-24: Step 2 EPV diagnostic completed (`docs/epv_amendment_2.md`).
  Amended six-block EPV = **6.214** (design columns = 56; mean CV train
  events = 348). Floor was ≥ 10. **Did not clear.** Per Step 2 gate,
  composite definitions are **not** locked for modeling, and **Step 4 was
  not run**.
