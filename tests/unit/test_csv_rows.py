import pytest
from pydantic import ValidationError

from de_ai_kb.services.csv_rows import SeedClaimRow, SeedSourceRow


def _valid_source_row(**overrides: str) -> dict[str, str]:
    row = {
        "source_key": "ROW_1",
        "title": "A Title",
        "publisher": "A Publisher",
        "source_type": "official_statistics",
        "tier": "A",
        "topics": "adoption|barriers",
        "geography": "DE",
        "language": "de",
        "url": "https://example.com/report",
        "access_policy": "metadata_only",
        "refresh_days": "90",
        "review_status": "discovery_verified",
        "notes": "",
    }
    row.update(overrides)
    return row


def test_valid_source_row_parses() -> None:
    row = SeedSourceRow.from_csv_row(_valid_source_row())
    assert row.source_key == "ROW_1"
    assert row.topics == ["adoption", "barriers"]
    assert row.canonical_url == "https://example.com/report"


def test_invalid_tier_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        SeedSourceRow.from_csv_row(_valid_source_row(tier="Z"))


def test_invalid_access_policy_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        SeedSourceRow.from_csv_row(_valid_source_row(access_policy="not_a_policy"))


def test_zero_refresh_days_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        SeedSourceRow.from_csv_row(_valid_source_row(refresh_days="0"))


def test_missing_source_key_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        SeedSourceRow.from_csv_row(_valid_source_row(source_key=""))


def test_invalid_url_raises_value_error() -> None:
    with pytest.raises(ValueError):
        SeedSourceRow.from_csv_row(_valid_source_row(url="not-a-url"))


def _valid_claim_row(**overrides: str) -> dict[str, str]:
    row = {
        "claim_key": "CLAIM_1",
        "source_key": "ROW_1",
        "claim_type": "adoption_statistic",
        "statement": "Some statement.",
        "normalized_value": "26",
        "unit": "percent",
        "geography": "DE",
        "company_size_scope": "All",
        "sample_size": "",
        "study_period": "2025",
        "locator": "table lines 1-2",
        "review_status": "evidence_checked",
        "notes": "",
    }
    row.update(overrides)
    return row


def test_valid_claim_row_parses() -> None:
    row = SeedClaimRow.from_csv_row(_valid_claim_row())
    assert row.claim_key == "CLAIM_1"


def test_claim_row_missing_locator_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        SeedClaimRow.from_csv_row(_valid_claim_row(locator=""))
