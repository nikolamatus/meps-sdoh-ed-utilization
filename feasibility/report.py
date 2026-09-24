"""
Decision gate and feasibility summary.

Triage floors are pre-registered in docs/pre_registration.md.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import config

GATE_NOTE = (
    "This gate is an engineering/research triage tool, not a validated "
    "statistical decision rule. Thresholds are conservative and pre-specified. "
    "GREEN requires evidence that the broader pre-2022 feature set (including "
    "SDOH) adds value beyond historical ED utilization."
)

# Pre-registered floors (docs/pre_registration.md) — set before seeing data.
MIN_USABLE_N = 1500
MIN_OUTCOME_EVENTS = 100
MIN_OUTCOME_PREVALENCE = 0.03
MIN_BASELINE_ROC_AUC = 0.55
MIN_INCREMENTAL_ROC_LIFT = 0.02
MIN_INCREMENTAL_PR_LIFT = 0.01
CORE_FAMILIES = frozenset({"prior_utilization", "demographics", "sdoh"})
ADDITIONAL_FAMILIES = frozenset({"health_status", "access", "socioeconomic"})
MIN_PRESENT_ALLOWED_FRACTION = 0.60


def _component(status: str, reasons: list[str]) -> dict:
    return {"status": status, "reasons": reasons}


def decide_gate(context: dict) -> tuple[str, dict]:
    usable_n = int(context.get("usable_n") or 0)
    n_events = int(context.get("n_outcome_events") or 0)
    prevalence = float(context.get("outcome_prevalence") or 0.0)
    families = set(context.get("families_present") or [])
    n_allowed = int(context.get("n_allowed_candidates") or 0)
    n_present = int(context.get("n_present_allowed") or 0)

    data_reasons = []
    if usable_n < MIN_USABLE_N:
        data_reasons.append(
            f"Analytic cohort ({usable_n}) is below the {MIN_USABLE_N} triage floor."
        )
    if n_events < MIN_OUTCOME_EVENTS:
        data_reasons.append(
            f"Primary-outcome events ({n_events}) are below the {MIN_OUTCOME_EVENTS} triage floor."
        )
    if prevalence < MIN_OUTCOME_PREVALENCE:
        data_reasons.append(
            f"Outcome prevalence ({prevalence:.2%}) is below {MIN_OUTCOME_PREVALENCE:.0%}."
        )
    missing_core = sorted(CORE_FAMILIES - families)
    if missing_core:
        data_reasons.append(f"Required predictor families missing from X: {missing_core}.")
    if not (families & ADDITIONAL_FAMILIES):
        data_reasons.append(
            "No health_status, access, or socioeconomic predictor is present."
        )
    if n_allowed and (n_present / n_allowed) < MIN_PRESENT_ALLOWED_FRACTION:
        data_reasons.append(
            f"Only {n_present}/{n_allowed} allowed candidates are present "
            f"(below {MIN_PRESENT_ALLOWED_FRACTION:.0%})."
        )
    if not context.get("longitudinal_ok", False):
        data_reasons.append("Documented dual cohort rule was not applied.")
    data = _component(
        "FAIL" if data_reasons else "PASS",
        data_reasons
        or ["Analytic sample and predictor families clear the triage floors."],
    )

    b2 = context.get("baseline2_roc_auc")
    baseline_reasons = []
    if b2 is None or b2 < MIN_BASELINE_ROC_AUC:
        baseline_reasons.append(
            f"Prior-year-ED baseline ROC-AUC ({b2}) does not clear the "
            f"{MIN_BASELINE_ROC_AUC} triage floor versus chance."
        )
    baseline = _component(
        "FAIL" if baseline_reasons else "PASS",
        baseline_reasons
        or [
            f"Prior-ED baseline ROC-AUC ({b2:.3f}) clears the triage floor."
        ],
    )

    full_roc = context.get("full_roc_auc")
    full_pr = context.get("full_pr_auc")
    ed_roc = context.get("best_ed_baseline_roc_auc")
    ed_pr = context.get("best_ed_baseline_pr_auc")
    incr_reasons = []
    if full_roc is None or full_pr is None or ed_roc is None or ed_pr is None:
        incr_reasons.append(
            "Incremental value cannot be assessed (missing full-model or "
            "ED-baseline ROC-AUC / PR-AUC)."
        )
        incremental = _component("INSUFFICIENT", incr_reasons)
    else:
        roc_lift = full_roc - ed_roc
        pr_lift = full_pr - ed_pr
        if roc_lift < MIN_INCREMENTAL_ROC_LIFT:
            incr_reasons.append(
                f"Full-model ROC-AUC lift vs best ED baseline is {roc_lift:.3f} "
                f"(need ≥ {MIN_INCREMENTAL_ROC_LIFT})."
            )
        if pr_lift < MIN_INCREMENTAL_PR_LIFT:
            incr_reasons.append(
                f"Full-model PR-AUC lift vs best ED baseline is {pr_lift:.3f} "
                f"(need ≥ {MIN_INCREMENTAL_PR_LIFT})."
            )
        incremental = _component(
            "FAIL" if incr_reasons else "PASS",
            incr_reasons
            or [
                f"Full model improves ROC-AUC by {roc_lift:.3f} and PR-AUC by "
                f"{pr_lift:.3f} over the best ED-history baseline."
            ],
        )

    ready_reasons = []
    if not context.get("leakage_ok", False):
        ready_reasons.append("Leakage invariant was not confirmed for this run.")
    if not context.get("calibration_produced", False):
        ready_reasons.append("Calibration table was not produced.")
    if not context.get("unique_persons", False):
        ready_reasons.append("Person identifiers are not unique.")
    if context.get("weighted", False):
        ready_reasons.append(
            "weighted=True is set but this pipeline does not implement "
            "survey-design-adjusted inference."
        )
    if not context.get("longitudinal_ok", False):
        ready_reasons.append("Cohort definition was not applied.")
    readiness = _component(
        "FAIL" if ready_reasons else "PASS",
        ready_reasons or ["Readiness checks passed."],
    )

    components = {
        "data_adequacy": data,
        "baseline_signal": baseline,
        "incremental_value": incremental,
        "readiness": readiness,
        "gate_note": GATE_NOTE,
    }

    if data["status"] == "FAIL" or readiness["status"] == "FAIL":
        color = "RED"
    elif incremental["status"] == "INSUFFICIENT":
        color = "YELLOW"
    elif baseline["status"] == "FAIL" or incremental["status"] == "FAIL":
        color = "YELLOW"
    else:
        color = "GREEN"
    return color, components


def write_summary(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
