"""
Central configuration for the SDOH-extended feasibility pipeline.

Predictor names are confirmed HC-245 longitudinal names (including
Round-5 SDOH suffixes). A feature may enter X only if it is
demonstrably available on or before the prediction cutoff (2021-12-31).
Unknown temporal availability fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = REPO_ROOT / "data" / "raw"
OUTPUTS_DIR = REPO_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"

MEPS_LONGITUDINAL = {
    "dataset_name": "MEPS HC-245: Panel 24, 4-Year Longitudinal Public Use File",
    "puf_id": "HC-245",
    "coverage": "2019-2022",
    "doc_url": "https://meps.ahrq.gov/data_stats/download_data/pufs/h245/h245doc.shtml",
    "expected_filename": "h245.dta",
    "stata_zip_hint": "Data File, Stata format (.zip) — listed on the HC-245 download page",
}

MEPS_SDOH_CONSOLIDATED = {
    "dataset_name": "MEPS HC-233: 2021 Full Year Consolidated Data File",
    "puf_id": "HC-233",
    "coverage": "2021",
    "doc_url": "https://meps.ahrq.gov/data_stats/download_data/pufs/h233/h233doc.shtml",
    "expected_filename": "h233.dta",
    "stata_zip_hint": "Data File, Stata format (.zip) — listed on the HC-233 download page",
    "required": False,
    "note": (
        "Optional. SDOH items for Panel 24 are already on HC-245 as SD*5. "
        "HC-233 is used only for DUPERSID cross-check and SDOHWT21F provenance."
    ),
}

PERSON_ID = "DUPERSID"
PANEL = "PANEL"
PANEL_24 = 24

YEARIND = "YEARIND"
ALL9RDS = "ALL9RDS"
LONGWT = "LONGWT"
VARSTR = "VARSTR"
VARPSU = "VARPSU"
SURVEY_DESIGN_VARS = (YEARIND, ALL9RDS, LONGWT, VARSTR, VARPSU)

YEARIND_ALL_FOUR_YEARS = 1

SDOH_ELIG = "SDOHELIG5"
SDOH_ELIG_HAS_DATA = 1

PREDICTION_CUTOFF_YEAR = 2021
OUTCOME_YEAR = 2022

SENTINEL_VALUES = frozenset({-1, -7, -8, -9})

ED_VISIT_VARS = {
    "year1_2019": "ERTOTY1",
    "year2_2020": "ERTOTY2",
    "year3_2021": "ERTOTY3",
    "year4_2022": "ERTOTY4",
}
PREDICTOR_ED_VARS = [
    ED_VISIT_VARS["year1_2019"],
    ED_VISIT_VARS["year2_2020"],
    ED_VISIT_VARS["year3_2021"],
]
OUTCOME_ED_VAR = ED_VISIT_VARS["year4_2022"]

RANDOM_SEED = 42
CV_RANDOM_STATE = 2021
HOLDOUT_FRACTION = 0.25
CV_N_SPLITS = 5
CV_N_REPEATS = 5


class FeatureMetadataError(ValueError):
    """Raised when allowed_by_cutoff disagrees with temporal availability."""


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    family: str
    description: str
    availability_year: int | None
    time_invariant: bool
    allowed_by_cutoff: bool
    treatment: str  # numeric | categorical | outcome | cohort_filter
    documentation_status: str

    def is_temporally_allowed(self) -> bool:
        if self.treatment in {"outcome", "cohort_filter"}:
            return False
        if self.time_invariant:
            return True
        if self.availability_year is None:
            return False
        return self.availability_year <= PREDICTION_CUTOFF_YEAR


def validate_feature_metadata(spec: FeatureSpec) -> None:
    computed = spec.is_temporally_allowed()
    if spec.treatment in {"outcome", "cohort_filter"}:
        if spec.allowed_by_cutoff:
            raise FeatureMetadataError(
                f"{spec.name}: treatment={spec.treatment} cannot have allowed_by_cutoff=True."
            )
        return
    if spec.allowed_by_cutoff != computed:
        raise FeatureMetadataError(
            f"{spec.name}: allowed_by_cutoff={spec.allowed_by_cutoff} disagrees "
            f"with temporal rule (availability_year={spec.availability_year}, "
            f"time_invariant={spec.time_invariant}, cutoff={PREDICTION_CUTOFF_YEAR}, "
            f"computed_allowed={computed})."
        )
    if spec.allowed_by_cutoff and spec.availability_year is None and not spec.time_invariant:
        raise FeatureMetadataError(
            f"{spec.name}: allowed_by_cutoff=True but temporal availability is unknown."
        )
    if (
        spec.availability_year is not None
        and spec.availability_year > PREDICTION_CUTOFF_YEAR
        and spec.allowed_by_cutoff
    ):
        raise FeatureMetadataError(
            f"{spec.name}: availability_year={spec.availability_year} is after "
            f"cutoff {PREDICTION_CUTOFF_YEAR}; cannot be allowed."
        )


def _f(
    name: str,
    family: str,
    description: str,
    availability_year: int | None,
    *,
    time_invariant: bool = False,
    treatment: str = "numeric",
    documentation_status: str = "confirmed",
) -> FeatureSpec:
    allowed = False
    if treatment not in {"outcome", "cohort_filter"}:
        tmp = FeatureSpec(
            name=name,
            family=family,
            description=description,
            availability_year=availability_year,
            time_invariant=time_invariant,
            allowed_by_cutoff=False,
            treatment=treatment,
            documentation_status=documentation_status,
        )
        allowed = tmp.is_temporally_allowed()
    spec = FeatureSpec(
        name=name,
        family=family,
        description=description,
        availability_year=availability_year,
        time_invariant=time_invariant,
        allowed_by_cutoff=allowed,
        treatment=treatment,
        documentation_status=documentation_status,
    )
    validate_feature_metadata(spec)
    return spec


# Companion non-SDOH lock set (HC-245 names).
BASELINE_FEATURES: list[FeatureSpec] = [
    _f("AGEY3X", "demographics", "Age as of 12/31/2021 (edited/imputed)", 2021, treatment="numeric"),
    _f("SEX", "demographics", "Sex (time-invariant)", None, time_invariant=True, treatment="categorical"),
    _f("RACETHX", "demographics", "Race/ethnicity edited/imputed (time-invariant)", None, time_invariant=True, treatment="categorical"),
    _f("REGIONY3", "demographics", "Census region as of 12/31/2021", 2021, treatment="categorical"),
    _f("MARRY6X", "demographics", "Marital status, Round 6 (2021), edited/imputed", 2021, treatment="categorical"),
    _f("RTHLTH6", "health_status", "Perceived health status, Round 6 (2021)", 2021, treatment="categorical"),
    _f("MNHLTH6", "health_status", "Perceived mental health status, Round 6 (2021)", 2021, treatment="categorical"),
    _f("INSCOVY3", "access", "Health insurance coverage indicator, 2021", 2021, treatment="categorical"),
    _f("HAVEUS6", "access", "Usual source of care provider, Round 6 (2021)", 2021, treatment="categorical"),
    _f("POVCATY3", "socioeconomic", "Family income as % of poverty line, 2021", 2021, treatment="categorical"),
    _f("TTLPY3X", "socioeconomic", "Person total income, 2021", 2021, treatment="numeric"),
    _f("EMPST6", "socioeconomic", "Employment status, Round 6 (2021)", 2021, treatment="categorical"),
    _f("ERTOTY1", "prior_utilization", "Emergency room visits, 2019", 2019, treatment="numeric"),
    _f("ERTOTY2", "prior_utilization", "Emergency room visits, 2020", 2020, treatment="numeric"),
    _f("ERTOTY3", "prior_utilization", "Emergency room visits, 2021", 2021, treatment="numeric"),
]

# Primary SDOH block (HC-245 Round-5 names). See docs/linkage_feasibility.md §5.
SDOH_FEATURES: list[FeatureSpec] = [
    _f("SDAFRDHOME5", "sdoh", "SDOH: affordable housing (R5/2021)", 2021, treatment="categorical"),
    _f("SDHOME5", "sdoh", "SDOH: satisfied with home (R5/2021)", 2021, treatment="categorical"),
    _f("SDLATERENT5", "sdoh", "SDOH: late rent/mortgage (R5/2021)", 2021, treatment="categorical"),
    _f("SDLATEUTIL5", "sdoh", "SDOH: late utility (R5/2021)", 2021, treatment="categorical"),
    _f("SDSHUTUTIL5", "sdoh", "SDOH: utility shutoff threat (R5/2021)", 2021, treatment="categorical"),
    _f("SDPROBPEST5", "sdoh", "SDOH: home pests (R5/2021)", 2021, treatment="categorical"),
    _f("SDPROBMOLD5", "sdoh", "SDOH: home mold (R5/2021)", 2021, treatment="categorical"),
    _f("SDPROBLEAD5", "sdoh", "SDOH: home lead (R5/2021)", 2021, treatment="categorical"),
    _f("SDPROBHEAT5", "sdoh", "SDOH: home heat (R5/2021)", 2021, treatment="categorical"),
    _f("SDPROBCOOK5", "sdoh", "SDOH: home cook (R5/2021)", 2021, treatment="categorical"),
    _f("SDPROBSMKDE5", "sdoh", "SDOH: smoke detector problem (R5/2021; HC-245 spelling)", 2021, treatment="categorical"),
    _f("SDPROBLEAKS5", "sdoh", "SDOH: water leaks (R5/2021)", 2021, treatment="categorical"),
    _f("SDPROBNONE5", "sdoh", "SDOH: no home problems (R5/2021)", 2021, treatment="categorical"),
    _f("SDWRRYFD5", "sdoh", "SDOH: worried about food (R5/2021)", 2021, treatment="categorical"),
    _f("SDNOFOOD5", "sdoh", "SDOH: food ran out (R5/2021)", 2021, treatment="categorical"),
    _f("SDHLTHFOOD5", "sdoh", "SDOH: places for healthy food (R5/2021)", 2021, treatment="categorical"),
    _f("SDNOTRANS5", "sdoh", "SDOH: no transport daily needs (R5/2021)", 2021, treatment="categorical"),
    _f("SDPUBTRANS5", "sdoh", "SDOH: public transportation access (R5/2021)", 2021, treatment="categorical"),
    _f("SDPAYBASICS5", "sdoh", "SDOH: hard to pay basics (R5/2021)", 2021, treatment="categorical"),
    _f("SDUNEXPEXP5", "sdoh", "SDOH: cover unexpected expense (R5/2021)", 2021, treatment="categorical"),
    _f("SDMISSCCLN5", "sdoh", "SDOH: missed card/loan payment (R5/2021)", 2021, treatment="categorical"),
    _f("SDDEBT5", "sdoh", "SDOH: collection contact (R5/2021)", 2021, treatment="categorical"),
    _f("SDFAMILY5", "sdoh", "SDOH: help from family (R5/2021)", 2021, treatment="categorical"),
    _f("SDFRIENDS5", "sdoh", "SDOH: help from friends (R5/2021)", 2021, treatment="categorical"),
    _f("SDCOMM5", "sdoh", "SDOH: help from community (R5/2021)", 2021, treatment="categorical"),
    _f("SDTLKPHN5", "sdoh", "SDOH: telephone others/week (R5/2021)", 2021, treatment="categorical"),
    _f("SDGETTGT5", "sdoh", "SDOH: see others/week (R5/2021)", 2021, treatment="categorical"),
    _f("SDCHURCH5", "sdoh", "SDOH: attend church/services (R5/2021)", 2021, treatment="categorical"),
    _f("SDCLUBORG5", "sdoh", "SDOH: club/org meetings/year (R5/2021)", 2021, treatment="categorical"),
    _f("SDCOMPAN5", "sdoh", "SDOH: lack companionship (R5/2021)", 2021, treatment="categorical"),
    _f("SDLEFTOUT5", "sdoh", "SDOH: feel left out (R5/2021)", 2021, treatment="categorical"),
    _f("SDISOL5", "sdoh", "SDOH: feel isolated (R5/2021)", 2021, treatment="categorical"),
    _f("SDSFCRIME5", "sdoh", "SDOH: safe from crime/violence (R5/2021)", 2021, treatment="categorical"),
    _f("SDPHYSHURT5", "sdoh", "SDOH: hurt by others (R5/2021)", 2021, treatment="categorical"),
    _f("SDINSULT5", "sdoh", "SDOH: insulted (R5/2021)", 2021, treatment="categorical"),
    _f("SDTHRHARM5", "sdoh", "SDOH: threatened harm (R5/2021)", 2021, treatment="categorical"),
    _f("SDSCREAM5", "sdoh", "SDOH: scream/curse (R5/2021)", 2021, treatment="categorical"),
    _f("SDHMDEPR5", "sdoh", "SDOH ACE: mental illness in home <18 (R5/2021)", 2021, treatment="categorical"),
    _f("SDHMALC5", "sdoh", "SDOH ACE: alcoholic in home <18 (R5/2021)", 2021, treatment="categorical"),
    _f("SDHMDRG5", "sdoh", "SDOH ACE: drugs in home <18 (R5/2021)", 2021, treatment="categorical"),
    _f("SDHMJAIL5", "sdoh", "SDOH ACE: sentenced person in home <18 (R5/2021)", 2021, treatment="categorical"),
    _f("SDHMDIV5", "sdoh", "SDOH ACE: split home <18 (R5/2021)", 2021, treatment="categorical"),
    _f("SDHMBEAT5", "sdoh", "SDOH ACE: abused <18 (R5/2021)", 2021, treatment="categorical"),
    _f("SDHURTCHLD5", "sdoh", "SDOH ACE: child hurt (R5/2021)", 2021, treatment="categorical"),
    _f("SDINSCHLD5", "sdoh", "SDOH ACE: child insult (R5/2021)", 2021, treatment="categorical"),
    _f("SDTCHCHLD5", "sdoh", "SDOH ACE: child touched (R5/2021)", 2021, treatment="categorical"),
    _f("SDTCHADLT5", "sdoh", "SDOH ACE: asked to touch (R5/2021)", 2021, treatment="categorical"),
    _f("SDFRCSXCH5", "sdoh", "SDOH ACE: forced (R5/2021)", 2021, treatment="categorical"),
]

OUTCOME_FEATURE = FeatureSpec(
    name="ERTOTY4",
    family="outcome",
    description="Emergency room visits, 2022 — PRIMARY OUTCOME, never a predictor",
    availability_year=2022,
    time_invariant=False,
    allowed_by_cutoff=False,
    treatment="outcome",
    documentation_status="confirmed",
)

COHORT_FILTER_FEATURE = FeatureSpec(
    name=SDOH_ELIG,
    family="cohort_filter",
    description="SDOH eligibility (R5/2021) — cohort filter, never a predictor",
    availability_year=2021,
    time_invariant=False,
    allowed_by_cutoff=False,
    treatment="cohort_filter",
    documentation_status="confirmed",
)

CANDIDATE_FEATURES: list[FeatureSpec] = (
    BASELINE_FEATURES + SDOH_FEATURES + [OUTCOME_FEATURE, COHORT_FILTER_FEATURE]
)

POST_CUTOFF_FEATURES: list[FeatureSpec] = [
    _f("AGEY4X", "demographics", "Age as of 12/31/2022 — post-cutoff", 2022, treatment="numeric"),
    _f("REGIONY4", "demographics", "Census region as of 12/31/2022 — post-cutoff", 2022, treatment="categorical"),
    _f("REGION8", "demographics", "Census region, Round 8 (2022) — post-cutoff", 2022, treatment="categorical"),
    _f("REGION9", "demographics", "Census region, Round 9 (2022) — post-cutoff", 2022, treatment="categorical"),
    _f("MARRY8X", "demographics", "Marital status, Round 8 (2022) — post-cutoff", 2022, treatment="categorical"),
    _f("RTHLTH8", "health_status", "Perceived health, Round 8 (2022) — post-cutoff", 2022, treatment="categorical"),
    _f("RTHLTH9", "health_status", "Perceived health, Round 9 (2022) — post-cutoff", 2022, treatment="categorical"),
    _f("MNHLTH8", "health_status", "Perceived mental health, Round 8 (2022) — post-cutoff", 2022, treatment="categorical"),
    _f("MNHLTH9", "health_status", "Perceived mental health, Round 9 (2022) — post-cutoff", 2022, treatment="categorical"),
    _f("INSCOVY4", "access", "Health insurance coverage indicator, 2022 — post-cutoff", 2022, treatment="categorical"),
    _f("HAVEUS8", "access", "Usual source of care, Round 8 (2022) — post-cutoff", 2022, treatment="categorical"),
    _f("POVCATY4", "socioeconomic", "Poverty category, 2022 — post-cutoff", 2022, treatment="categorical"),
    _f("TTLPY4X", "socioeconomic", "Person total income, 2022 — post-cutoff", 2022, treatment="numeric"),
    _f("EMPST8", "socioeconomic", "Employment status, Round 8 (2022) — post-cutoff", 2022, treatment="categorical"),
    _f("EMPST9", "socioeconomic", "Employment status, Round 9 (2022) — post-cutoff", 2022, treatment="categorical"),
]

for _spec in CANDIDATE_FEATURES + POST_CUTOFF_FEATURES:
    validate_feature_metadata(_spec)

FEATURE_INDEX: dict[str, FeatureSpec] = {s.name: s for s in CANDIDATE_FEATURES}
for _spec in POST_CUTOFF_FEATURES:
    FEATURE_INDEX.setdefault(_spec.name, _spec)

POST_CUTOFF_NAMES = frozenset(
    {s.name for s in POST_CUTOFF_FEATURES} | {OUTCOME_ED_VAR}
)

BLOCK_DEFINITIONS: dict[str, tuple[str, ...]] = {
    "age": ("AGEY3X",),
    "demographics": ("SEX", "RACETHX", "REGIONY3", "MARRY6X"),
    "health_status": ("RTHLTH6", "MNHLTH6"),
    "access": ("INSCOVY3", "HAVEUS6"),
    "socioeconomic": ("POVCATY3", "TTLPY3X", "EMPST6"),
    "prior_utilization": tuple(PREDICTOR_ED_VARS),
    "sdoh": tuple(s.name for s in SDOH_FEATURES),
}


def allowed_predictor_specs() -> list[FeatureSpec]:
    return [
        s
        for s in CANDIDATE_FEATURES
        if s.allowed_by_cutoff and s.treatment in {"numeric", "categorical"}
    ]


def sdoh_predictor_names() -> list[str]:
    return [s.name for s in SDOH_FEATURES if s.allowed_by_cutoff]
