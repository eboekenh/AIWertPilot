import pytest

from de_ai_kb.domain.url import canonicalize_url


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://Example.com/Path", "https://example.com/Path"),
        ("https://example.com:443/path", "https://example.com/path"),
        ("http://example.com:80/path", "http://example.com/path"),
        ("http://example.com:8080/path", "http://example.com:8080/path"),
        ("https://example.com/path/", "https://example.com/path"),
        ("https://example.com/", "https://example.com/"),
        ("https://example.com/path#section", "https://example.com/path"),
        ("https://example.com/path?b=2&a=1", "https://example.com/path?a=1&b=2"),
        (
            "https://example.com/page?utm_source=x&id=42",
            "https://example.com/page?id=42",
        ),
        (
            "https://example.com/page?gclid=abc&fbclid=def&keep=1",
            "https://example.com/page?keep=1",
        ),
    ],
)
def test_canonicalize_url_table(raw: str, expected: str) -> None:
    assert canonicalize_url(raw) == expected


def test_canonicalize_url_preserves_meaningful_query_params() -> None:
    # Statistics-office style report/table identifiers must never be dropped.
    raw = "https://www.destatis.de/report?table=ikti-unternehmen&year=2025"
    canonical = canonicalize_url(raw)
    assert "table=ikti-unternehmen" in canonical
    assert "year=2025" in canonical


def test_canonicalize_url_is_idempotent() -> None:
    raw = "https://Example.com:443/Path/?b=2&a=1&utm_source=x#frag"
    once = canonicalize_url(raw)
    twice = canonicalize_url(once)
    assert once == twice


@pytest.mark.parametrize("bad_url", ["not-a-url", "", "example.com/path", "ftp:///nohost"])
def test_canonicalize_url_rejects_non_absolute(bad_url: str) -> None:
    with pytest.raises(ValueError):
        canonicalize_url(bad_url)
