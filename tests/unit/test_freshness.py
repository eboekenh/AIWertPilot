from datetime import UTC, datetime, timedelta

import pytest

from de_ai_kb.domain.enums import FreshnessState
from de_ai_kb.domain.freshness import compute_freshness_state

NOW = datetime(2026, 7, 18, 12, 0, 0, tzinfo=UTC)


def test_unknown_when_never_verified() -> None:
    state = compute_freshness_state(last_verified_at=None, refresh_interval_days=90, now=NOW)
    assert state is FreshnessState.UNKNOWN


def test_fresh_immediately_after_verification() -> None:
    state = compute_freshness_state(last_verified_at=NOW, refresh_interval_days=90, now=NOW)
    assert state is FreshnessState.FRESH


def test_fresh_just_before_due_soon_window() -> None:
    # 90-day interval -> due_soon window is round(90*0.2)=18 days; day 71 is
    # still fresh (age < 72).
    verified = NOW - timedelta(days=71, hours=23)
    state = compute_freshness_state(last_verified_at=verified, refresh_interval_days=90, now=NOW)
    assert state is FreshnessState.FRESH


def test_due_soon_at_threshold_boundary() -> None:
    verified = NOW - timedelta(days=72)
    state = compute_freshness_state(last_verified_at=verified, refresh_interval_days=90, now=NOW)
    assert state is FreshnessState.DUE_SOON


def test_fresh_at_one_second_before_due_soon_boundary() -> None:
    verified = NOW - timedelta(days=72) + timedelta(seconds=1)
    state = compute_freshness_state(last_verified_at=verified, refresh_interval_days=90, now=NOW)
    assert state is FreshnessState.FRESH


def test_stale_exactly_at_interval_boundary() -> None:
    verified = NOW - timedelta(days=90)
    state = compute_freshness_state(last_verified_at=verified, refresh_interval_days=90, now=NOW)
    assert state is FreshnessState.STALE


def test_fresh_one_second_before_interval_boundary() -> None:
    verified = NOW - timedelta(days=90) + timedelta(seconds=1)
    state = compute_freshness_state(last_verified_at=verified, refresh_interval_days=90, now=NOW)
    assert state is FreshnessState.DUE_SOON


def test_stale_long_after_interval() -> None:
    verified = NOW - timedelta(days=400)
    state = compute_freshness_state(last_verified_at=verified, refresh_interval_days=90, now=NOW)
    assert state is FreshnessState.STALE


def test_short_interval_due_soon_minimum_one_day() -> None:
    # 7-day interval -> due_soon window = round(7*0.2)=1 (matches the
    # minimum), so day 6 is due_soon.
    verified = NOW - timedelta(days=6)
    state = compute_freshness_state(last_verified_at=verified, refresh_interval_days=7, now=NOW)
    assert state is FreshnessState.DUE_SOON


def test_rejects_non_positive_interval() -> None:
    with pytest.raises(ValueError):
        compute_freshness_state(last_verified_at=NOW, refresh_interval_days=0, now=NOW)
