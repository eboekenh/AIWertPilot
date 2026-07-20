"""Pure validation of rights-review resolution outcomes.

A rights review is only meaningful if it produces an explicit, internally
consistent rights_status/access_policy pair — never an inference like
"approved therefore full_text_allowed" (RESEARCH_PROTOCOL.md §10: a public
URL is not permission to retain full text; conservative defaults only
change on an explicit, documented rights basis).
"""

from __future__ import annotations

from de_ai_kb.domain.enums import AccessPolicy, RightsStatus

# NEEDS_REVIEW is deliberately absent: it means "not yet reviewed" and can
# never be the *outcome* of a review decision. BLOCKED only ever pairs with
# AccessPolicy.BLOCKED — a blocked rights result must never permit any
# retention. REVIEWED_RESTRICTED excludes FULL_TEXT_ALLOWED — restricted
# rights must not grant full-text retention.
ALLOWED_ACCESS_POLICIES_BY_RIGHTS_STATUS: dict[RightsStatus, frozenset[AccessPolicy]] = {
    RightsStatus.REVIEWED_ALLOWED: frozenset(
        {AccessPolicy.METADATA_ONLY, AccessPolicy.SHORT_EVIDENCE, AccessPolicy.FULL_TEXT_ALLOWED}
    ),
    RightsStatus.REVIEWED_RESTRICTED: frozenset({AccessPolicy.METADATA_ONLY, AccessPolicy.SHORT_EVIDENCE}),
    RightsStatus.BLOCKED: frozenset({AccessPolicy.BLOCKED}),
}


def validate_rights_resolution(rights_status: RightsStatus, access_policy: AccessPolicy) -> None:
    """Raises ValueError if the pair is not a valid, explicit reviewed outcome."""
    allowed = ALLOWED_ACCESS_POLICIES_BY_RIGHTS_STATUS.get(rights_status)
    if allowed is None:
        raise ValueError(
            f"rights_status {rights_status.value!r} is not a valid reviewed outcome "
            "(a rights review must resolve to reviewed_allowed, reviewed_restricted, or blocked)"
        )
    if access_policy not in allowed:
        allowed_values = sorted(p.value for p in allowed)
        raise ValueError(
            f"access_policy {access_policy.value!r} is not permitted for "
            f"rights_status {rights_status.value!r} (allowed: {allowed_values})"
        )
