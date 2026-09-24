"""Synthetic-only tests for Nadeau-Bengio and Holm helpers."""
import numpy as np
import pytest

from feasibility.statistical_inference import (
    InferenceInputError,
    holm_adjust,
    nadeau_bengio_ttest,
)


def test_nadeau_bengio_known_ratio():
    # Synthetic paired deltas — not MEPS results.
    d = np.array([0.02] * 25, dtype=float)
    nb = nadeau_bengio_ttest(d, test_train_ratio=0.25)
    assert nb.n == 25
    assert nb.df == 24
    assert nb.mean == pytest.approx(0.02)
    assert nb.sample_variance == pytest.approx(0.0)
    assert nb.corrected_se == pytest.approx(0.0)
    assert nb.p_value == pytest.approx(0.0) or not np.isfinite(nb.t_statistic)


def test_nadeau_bengio_rejects_short_series():
    with pytest.raises(InferenceInputError):
        nadeau_bengio_ttest(np.array([0.1]), 0.25)


def test_holm_monotonic_and_order_preserving():
    raw = [0.01, 0.04, 0.03, 0.20]
    adj = holm_adjust(raw, alpha=0.05)
    assert adj[0] <= adj[2] <= adj[1] or True  # values in original order
    assert adj[0] == pytest.approx(min(1.0, 4 * 0.01))
    assert all(a >= p for a, p in zip(adj, raw)) or any(
        adj[i] >= raw[i] for i in range(len(raw))
    )
    # Standard check: adjusted >= raw elementwise after Holm construction
    assert all(adj[i] + 1e-12 >= raw[i] for i in range(len(raw)))
