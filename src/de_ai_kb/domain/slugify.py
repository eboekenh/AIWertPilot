"""Deterministic ASCII slug generation for taxonomy/business records."""

from __future__ import annotations

import re

_UMLAUT_MAP = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    value = value.lower().translate(_UMLAUT_MAP)
    value = _NON_ALNUM.sub("-", value).strip("-")
    return value
