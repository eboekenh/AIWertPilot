from de_ai_kb.main import _parse_cors_origins


def test_parse_cors_origins_empty_string_returns_no_origins() -> None:
    assert _parse_cors_origins("") == []


def test_parse_cors_origins_whitespace_only_returns_no_origins() -> None:
    assert _parse_cors_origins("   ") == []


def test_parse_cors_origins_splits_and_strips() -> None:
    assert _parse_cors_origins(" http://localhost:3000 , http://example.com ") == [
        "http://localhost:3000",
        "http://example.com",
    ]


def test_parse_cors_origins_drops_empty_segments() -> None:
    assert _parse_cors_origins("http://localhost:3000,,") == ["http://localhost:3000"]
