"""Deterministic text similarity for duplicate-candidate detection.

Uses difflib's SequenceMatcher, which is deterministic (no randomness, no
external model) and stable across runs — required for reproducible dedup
tests and for never silently merging records based on ambiguous scores.
"""

from __future__ import annotations

from difflib import SequenceMatcher

TITLE_SIMILARITY_THRESHOLD = 0.85


def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()
