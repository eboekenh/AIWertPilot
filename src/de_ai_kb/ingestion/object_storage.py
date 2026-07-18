"""Object-storage abstraction: a local-filesystem implementation for
development plus an S3-compatible Protocol, so a real S3/MinIO backend can
be dropped in later without touching callers. No cloud credentials required
in Foundation Release 1.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ObjectStorage(Protocol):
    async def put(self, key: str, data: bytes) -> str:
        """Store data under key, return a storage_uri."""
        ...

    async def get(self, key: str) -> bytes: ...


class LocalFilesystemObjectStorage:
    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    async def put(self, key: str, data: bytes) -> str:
        path = self._root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"file://{path.resolve()}"

    async def get(self, key: str) -> bytes:
        return (self._root / key).read_bytes()
