"""URL canonicalization for source deduplication.

Canonicalization must not destroy meaningful query parameters (e.g. table or
report identifiers on statistics-office pages), so it only lowercases the
scheme/host, strips default ports and the fragment, drops a small denylist of
known tracking parameters, sorts remaining query parameters for determinism,
and normalizes a trailing slash. Both the original and canonical URL are
always stored separately by callers.
"""

from __future__ import annotations

from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit

_DEFAULT_PORTS = {"http": 80, "https": 443}

_TRACKING_PARAM_DENYLIST = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "gclid",
    "fbclid",
    "mc_cid",
    "mc_eid",
    "ref",
}


def canonicalize_url(raw_url: str) -> str:
    """Return a deterministic canonical form of raw_url.

    Raises ValueError if raw_url has no scheme/host (not a usable absolute URL).
    """
    parts = urlsplit(raw_url.strip())
    if not parts.scheme or not parts.netloc:
        raise ValueError(f"URL is not absolute (missing scheme or host): {raw_url!r}")

    scheme = parts.scheme.lower()
    hostname = (parts.hostname or "").lower()
    if not hostname:
        raise ValueError(f"URL has no host: {raw_url!r}")

    port = parts.port
    netloc = hostname
    if port is not None and port != _DEFAULT_PORTS.get(scheme):
        netloc = f"{hostname}:{port}"
    if parts.username:
        userinfo = parts.username
        if parts.password:
            userinfo += f":{parts.password}"
        netloc = f"{userinfo}@{netloc}"

    path = parts.path or "/"
    # Normalize percent-encoding, then re-encode deterministically.
    path = quote(unquote(path), safe="/%")
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
        if not path:
            path = "/"

    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in _TRACKING_PARAM_DENYLIST
    ]
    query_pairs.sort(key=lambda kv: (kv[0], kv[1]))
    query = urlencode(query_pairs)

    # Fragment is dropped: fragments do not identify distinct server resources.
    return urlunsplit((scheme, netloc, path, query, ""))
