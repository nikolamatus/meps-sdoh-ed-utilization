"""
SDOH domain composites per docs/pre_registration_amendment_2.md.

Measurement-only construction: hardship indicator counts by domain.
Higher composite = more hardship.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import features

# Ambiguous multi-category collapse codes seen on HC-245 SDOH items.
AMBIGUOUS_CODES = frozenset({5, 6, 7, 8})


@dataclass(frozen=True)
class DomainSpec:
    name: str
    items: tuple[str, ...]
    # item -> frozenset of values that endorse hardship
    endorse: dict[str, frozenset[int]]


DOMAIN_SPECS: tuple[DomainSpec, ...] = (
    DomainSpec(
        name="SDOH_HOUSING",
        items=(
            "SDAFRDHOME5",
            "SDHOME5",
            "SDLATERENT5",
            "SDLATEUTIL5",
            "SDSHUTUTIL5",
            "SDPROBPEST5",
            "SDPROBMOLD5",
            "SDPROBLEAD5",
            "SDPROBHEAT5",
            "SDPROBCOOK5",
            "SDPROBSMKDE5",
            "SDPROBLEAKS5",
        ),
        endorse={
            "SDAFRDHOME5": frozenset({4, 5}),
            "SDHOME5": frozenset({4, 5}),
            "SDLATERENT5": frozenset({1}),
            "SDLATEUTIL5": frozenset({1}),
            "SDSHUTUTIL5": frozenset({1}),
            "SDPROBPEST5": frozenset({1}),
            "SDPROBMOLD5": frozenset({1}),
            "SDPROBLEAD5": frozenset({1}),
            "SDPROBHEAT5": frozenset({1}),
            "SDPROBCOOK5": frozenset({1}),
            "SDPROBSMKDE5": frozenset({1}),
            "SDPROBLEAKS5": frozenset({1}),
        },
    ),
    DomainSpec(
        name="SDOH_FOOD",
        items=("SDWRRYFD5", "SDNOFOOD5", "SDHLTHFOOD5"),
        endorse={
            "SDWRRYFD5": frozenset({1, 2}),
            "SDNOFOOD5": frozenset({1, 2}),
            "SDHLTHFOOD5": frozenset({4, 5}),
        },
    ),
    DomainSpec(
        name="SDOH_TRANS",
        items=("SDNOTRANS5", "SDPUBTRANS5"),
        endorse={
            "SDNOTRANS5": frozenset({1}),
            "SDPUBTRANS5": frozenset({4, 5}),
        },
    ),
    DomainSpec(
        name="SDOH_FINANCIAL",
        items=("SDPAYBASICS5", "SDUNEXPEXP5", "SDMISSCCLN5", "SDDEBT5"),
        endorse={
            "SDPAYBASICS5": frozenset({1}),
            "SDUNEXPEXP5": frozenset({1, 2}),
            "SDMISSCCLN5": frozenset({1}),
            "SDDEBT5": frozenset({1}),
        },
    ),
    DomainSpec(
        name="SDOH_SOCIAL",
        items=(
            "SDFAMILY5",
            "SDFRIENDS5",
            "SDCOMM5",
            "SDTLKPHN5",
            "SDGETTGT5",
            "SDCHURCH5",
            "SDCLUBORG5",
            "SDCOMPAN5",
            "SDLEFTOUT5",
            "SDISOL5",
        ),
        endorse={
            "SDFAMILY5": frozenset({3, 4}),
            "SDFRIENDS5": frozenset({3, 4}),
            "SDCOMM5": frozenset({3, 4}),
            "SDTLKPHN5": frozenset({0}),
            "SDGETTGT5": frozenset({0}),
            "SDCHURCH5": frozenset({0}),
            "SDCLUBORG5": frozenset({0}),
            "SDCOMPAN5": frozenset({3, 4}),
            "SDLEFTOUT5": frozenset({4}),
            "SDISOL5": frozenset({4}),
        },
    ),
    DomainSpec(
        name="SDOH_SAFETY",
        items=(
            "SDSFCRIME5",
            "SDPHYSHURT5",
            "SDINSULT5",
            "SDTHRHARM5",
            "SDSCREAM5",
        ),
        endorse={
            "SDSFCRIME5": frozenset({4, 5}),
            "SDPHYSHURT5": frozenset({2, 3, 4, 5}),
            "SDINSULT5": frozenset({3, 4, 5}),
            "SDTHRHARM5": frozenset({2, 3, 4, 5}),
            "SDSCREAM5": frozenset({3, 4, 5}),
        },
    ),
    DomainSpec(
        name="SDOH_ACE",
        items=(
            "SDHMDEPR5",
            "SDHMALC5",
            "SDHMDRG5",
            "SDHMJAIL5",
            "SDHMDIV5",
            "SDHMBEAT5",
            "SDHURTCHLD5",
            "SDINSCHLD5",
            "SDTCHCHLD5",
            "SDTCHADLT5",
            "SDFRCSXCH5",
        ),
        endorse={
            "SDHMDEPR5": frozenset({1}),
            "SDHMALC5": frozenset({1}),
            "SDHMDRG5": frozenset({1}),
            "SDHMJAIL5": frozenset({1}),
            "SDHMDIV5": frozenset({1}),
            "SDHMBEAT5": frozenset({2, 3}),
            "SDHURTCHLD5": frozenset({2, 3}),
            "SDINSCHLD5": frozenset({2, 3}),
            "SDTCHCHLD5": frozenset({2, 3}),
            "SDTCHADLT5": frozenset({2, 3}),
            "SDFRCSXCH5": frozenset({2, 3}),
        },
    ),
)

COMPOSITE_NAMES = tuple(d.name for d in DOMAIN_SPECS)


def _usable_numeric(series: pd.Series) -> pd.Series:
    """Sentinel/negative → NA; ambiguous collapse codes → NA."""
    s = features.recode_sentinels(series)
    return s.mask(s.isin(AMBIGUOUS_CODES))


def _min_usable_items(m: int) -> int:
    return int(np.ceil(0.5 * m))


def build_domain_composite(df: pd.DataFrame, spec: DomainSpec) -> pd.Series:
    m = len(spec.items)
    min_k = _min_usable_items(m)
    usable_flags = []
    endorse_flags = []
    for item in spec.items:
        if item not in df.columns:
            raise KeyError(f"Missing SDOH item required for {spec.name}: {item}")
        vals = _usable_numeric(df[item])
        usable_flags.append(vals.notna())
        endorse_flags.append(vals.isin(spec.endorse[item]))
    usable_mat = pd.concat(usable_flags, axis=1)
    endorse_mat = pd.concat(endorse_flags, axis=1)
    k = usable_mat.sum(axis=1)
    counts = endorse_mat.sum(axis=1).astype(float)
    out = pd.Series(np.nan, index=df.index, dtype=float)
    ok = k >= min_k
    out.loc[ok] = counts.loc[ok]
    return out


def add_sdoh_composites(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for spec in DOMAIN_SPECS:
        out[spec.name] = build_domain_composite(out, spec)
    return out
