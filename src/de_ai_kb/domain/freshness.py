"""Deterministic freshness calculation.

RESEARCH_PROTOCOL.md §9 defines default refresh intervals by source/record
category and four freshness states: fresh, due_soon, stale, unknown.
`due_soon` is defined as the final 20% of the refresh interval before it is
due (minimum 1 day), so a 90-day interval becomes due_soon starting 18 days
before the due date. This is a pure function of two timestamps and an
interval — no I/O, no clock mutation, fully unit-testable at exact
boundaries.
"""

from __future__ import annotations

from datetime import datetime

from de_ai_kb.domain.enums import FreshnessState

# Default refresh intervals in days, by category, per RESEARCH_PROTOCOL.md §9
# / CLAUDE_CODE_MASTER_PROMPT.md §8. Individual records may override via
# their own refresh_interval_days column; these are only the seeding
# defaults used when a category is registered without an explicit override.
DEFAULT_REFRESH_INTERVAL_DAYS: dict[str, int] = {
    "regulatory_deadline": 10,
    "training_availability": 30,
    "vendor_product": 30,
    "market_statistics": 90,
    "research_standards": 180,
    "evergreen_methodology": 365,
}

_DUE_SOON_FRACTION = 0.2
_DUE_SOON_MIN_DAYS = 1


def compute_freshness_state(
    *,
    last_verified_at: datetime | None,
    refresh_interval_days: int,
    now: datetime,
) -> FreshnessState:
    if last_verified_at is None:
        return FreshnessState.UNKNOWN
    if refresh_interval_days <= 0:
        raise ValueError("refresh_interval_days must be positive")

    age_days = (now - last_verified_at).total_seconds() / 86400
    due_soon_window = max(_DUE_SOON_MIN_DAYS, round(refresh_interval_days * _DUE_SOON_FRACTION))
    due_soon_threshold = refresh_interval_days - due_soon_window

    if age_days >= refresh_interval_days:
        return FreshnessState.STALE
    if age_days >= due_soon_threshold:
        return FreshnessState.DUE_SOON
    return FreshnessState.FRESH


def compute_next_review_at(
    *, last_verified_at: datetime | None, refresh_interval_days: int
) -> datetime | None:
    if last_verified_at is None:
        return None
    from datetime import timedelta

    return last_verified_at + timedelta(days=refresh_interval_days)
