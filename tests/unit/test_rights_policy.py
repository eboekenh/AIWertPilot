import pytest

from de_ai_kb.domain.enums import AccessPolicy, RightsStatus
from de_ai_kb.domain.rights_policy import validate_rights_resolution


@pytest.mark.parametrize(
    ("rights_status", "access_policy"),
    [
        (RightsStatus.REVIEWED_ALLOWED, AccessPolicy.METADATA_ONLY),
        (RightsStatus.REVIEWED_ALLOWED, AccessPolicy.SHORT_EVIDENCE),
        (RightsStatus.REVIEWED_ALLOWED, AccessPolicy.FULL_TEXT_ALLOWED),
        (RightsStatus.REVIEWED_RESTRICTED, AccessPolicy.METADATA_ONLY),
        (RightsStatus.REVIEWED_RESTRICTED, AccessPolicy.SHORT_EVIDENCE),
        (RightsStatus.BLOCKED, AccessPolicy.BLOCKED),
    ],
)
def test_valid_combinations_do_not_raise(rights_status: RightsStatus, access_policy: AccessPolicy) -> None:
    validate_rights_resolution(rights_status, access_policy)  # must not raise


@pytest.mark.parametrize(
    ("rights_status", "access_policy"),
    [
        (RightsStatus.REVIEWED_RESTRICTED, AccessPolicy.FULL_TEXT_ALLOWED),
        (RightsStatus.BLOCKED, AccessPolicy.SHORT_EVIDENCE),
        (RightsStatus.BLOCKED, AccessPolicy.FULL_TEXT_ALLOWED),
        (RightsStatus.BLOCKED, AccessPolicy.METADATA_ONLY),
    ],
)
def test_invalid_combinations_raise(rights_status: RightsStatus, access_policy: AccessPolicy) -> None:
    with pytest.raises(ValueError, match="not permitted"):
        validate_rights_resolution(rights_status, access_policy)


def test_needs_review_is_never_a_valid_resolution() -> None:
    with pytest.raises(ValueError, match="not a valid reviewed outcome"):
        validate_rights_resolution(RightsStatus.NEEDS_REVIEW, AccessPolicy.METADATA_ONLY)
