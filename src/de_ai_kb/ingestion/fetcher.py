"""Fetcher interface for a later ingestion release. No live fetching in
Foundation Release 1 — this module defines the boundary only, so Release 2
can implement a real httpx-based, rate-limited, robots-respecting fetcher
against it without changing callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class FetchResult:
    final_url: str
    http_status: int
    media_type: str | None
    content: bytes
    etag: str | None = None
    last_modified: str | None = None


class Fetcher(Protocol):
    async def fetch(self, url: str, *, user_agent: str) -> FetchResult: ...
