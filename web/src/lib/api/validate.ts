/**
 * Runtime validation for every Server Action payload in actions.ts.
 *
 * TypeScript types (SourceCreateInput, etc.) are a compile-time convenience
 * for callers within this codebase — they are erased at build time and are
 * not a runtime security boundary. A Server Action is itself a callable
 * HTTP endpoint (Next.js gives it a stable action ID), so a request built
 * outside this app's own UI can send any JSON body it likes, regardless of
 * what the TS signature declares. Every validator here therefore takes
 * `unknown`, checks the actual shape and value of the data at runtime, and
 * explicitly reconstructs a clean object containing only allowed fields —
 * it never spreads or forwards the raw input, so a forbidden/extra field
 * (e.g. a `status` slipped into a source-creation payload) can never reach
 * the backend, and unknown/malformed input is rejected before the backend
 * is ever contacted.
 *
 * These validators check shape, type, and enum membership only — never the
 * backend's cross-field business rules (e.g. which rights_status/
 * access_policy combinations are consistent, or which status transitions
 * are legal from a given current status). Those remain the backend's sole
 * authority; duplicating them here would risk drifting out of sync with
 * domain/rights_policy.py and domain/enums.py and silently under- or
 * over-restricting what a request can attempt.
 */

import {
  ACCESS_POLICIES,
  REVIEW_ITEM_STATUSES,
  SOURCE_STATUSES,
  SOURCE_TIERS,
  TDM_OPT_OUT_STATUSES,
  RIGHTS_STATUSES,
  type ReviewDecisionInput,
  type RightsReviewDecisionInput,
  type SourceBlockInput,
  type SourceCreateInput,
  type SourceTransitionInput,
  type SourceUpdateInput,
} from "./types";

export class ValidationError extends Error {
  details: Record<string, unknown>;

  constructor(message: string, details: Record<string, unknown> = {}) {
    super(message);
    this.name = "ValidationError";
    this.details = details;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function assertRecord(value: unknown): Record<string, unknown> {
  if (!isRecord(value)) {
    throw new ValidationError("Ungültige Anfrage: Es wurde ein Objekt erwartet.");
  }
  return value;
}

function assertNoForbiddenKeys(input: Record<string, unknown>, allowed: readonly string[]): void {
  const extra = Object.keys(input).filter((key) => !allowed.includes(key));
  if (extra.length > 0) {
    throw new ValidationError(`Unzulässige Felder in der Anfrage: ${extra.join(", ")}.`, {
      rejected_fields: extra,
    });
  }
}

function requireNonBlankString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new ValidationError(`Feld "${field}" muss ein nicht-leerer Text sein.`, { field });
  }
  return value.trim();
}

function optionalString(value: unknown, field: string): string | undefined {
  if (value === undefined) return undefined;
  if (typeof value !== "string") {
    throw new ValidationError(`Feld "${field}" muss Text sein.`, { field });
  }
  return value;
}

function optionalNullableString(value: unknown, field: string): string | null | undefined {
  if (value === undefined) return undefined;
  if (value === null) return null;
  if (typeof value !== "string") {
    throw new ValidationError(`Feld "${field}" muss Text oder null sein.`, { field });
  }
  return value;
}

function optionalStringArray(value: unknown, field: string): string[] | undefined {
  if (value === undefined) return undefined;
  if (!Array.isArray(value) || !value.every((item) => typeof item === "string")) {
    throw new ValidationError(`Feld "${field}" muss eine Liste von Texten sein.`, { field });
  }
  return value;
}

function optionalPositiveInt(value: unknown, field: string): number | undefined {
  if (value === undefined) return undefined;
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
    throw new ValidationError(`Feld "${field}" muss eine positive Zahl sein.`, { field });
  }
  return value;
}

function requireEnum<T extends string>(value: unknown, allowed: readonly T[], field: string): T {
  if (typeof value !== "string" || !(allowed as readonly string[]).includes(value)) {
    throw new ValidationError(`Feld "${field}" muss einer der folgenden Werte sein: ${allowed.join(", ")}.`, {
      field,
      allowed,
    });
  }
  return value as T;
}

function optionalNullableEnum<T extends string>(
  value: unknown,
  allowed: readonly T[],
  field: string,
): T | null | undefined {
  if (value === undefined) return undefined;
  if (value === null) return null;
  return requireEnum(value, allowed, field);
}

// --- Source creation ---------------------------------------------------

const SOURCE_CREATE_FIELDS = [
  "source_key",
  "title",
  "publisher",
  "original_url",
  "source_type",
  "tier",
  "language_code",
  "geography_codes",
  "jurisdiction_codes",
  "topic_tags",
  "refresh_interval_days",
  "notes",
] as const;

export function validateSourceCreateInput(raw: unknown): SourceCreateInput {
  const input = assertRecord(raw);
  assertNoForbiddenKeys(input, SOURCE_CREATE_FIELDS);
  return {
    source_key: requireNonBlankString(input.source_key, "source_key"),
    title: requireNonBlankString(input.title, "title"),
    publisher: requireNonBlankString(input.publisher, "publisher"),
    original_url: requireNonBlankString(input.original_url, "original_url"),
    source_type: requireNonBlankString(input.source_type, "source_type"),
    tier: requireEnum(input.tier, SOURCE_TIERS, "tier"),
    language_code: optionalString(input.language_code, "language_code"),
    geography_codes: optionalStringArray(input.geography_codes, "geography_codes"),
    jurisdiction_codes: optionalStringArray(input.jurisdiction_codes, "jurisdiction_codes"),
    topic_tags: optionalStringArray(input.topic_tags, "topic_tags"),
    refresh_interval_days: optionalPositiveInt(input.refresh_interval_days, "refresh_interval_days"),
    notes: optionalNullableString(input.notes, "notes"),
  };
}

// --- Source metadata update (PATCH) -------------------------------------

const SOURCE_UPDATE_FIELDS = ["title", "publisher", "tier", "topic_tags", "refresh_interval_days", "notes"] as const;

export function validateSourceUpdateInput(raw: unknown): SourceUpdateInput {
  const input = assertRecord(raw);
  assertNoForbiddenKeys(input, SOURCE_UPDATE_FIELDS);
  return {
    title: optionalString(input.title, "title"),
    publisher: optionalString(input.publisher, "publisher"),
    tier: input.tier === undefined ? undefined : requireEnum(input.tier, SOURCE_TIERS, "tier"),
    topic_tags: optionalStringArray(input.topic_tags, "topic_tags"),
    refresh_interval_days: optionalPositiveInt(input.refresh_interval_days, "refresh_interval_days"),
    notes: optionalNullableString(input.notes, "notes"),
  };
}

// --- Source status transition --------------------------------------------

const SOURCE_TRANSITION_FIELDS = ["new_status", "reason"] as const;

/** Excludes "blocked" — the backend rejects it via /transition regardless,
 * but this closes the gap for any caller of the Server Action that isn't
 * going through the compile-time-typed SourceTransitionForm (which already
 * never offers it as an option). */
const TRANSITIONABLE_STATUSES = SOURCE_STATUSES.filter((status) => status !== "blocked");

export function validateSourceTransitionInput(raw: unknown): SourceTransitionInput {
  const input = assertRecord(raw);
  assertNoForbiddenKeys(input, SOURCE_TRANSITION_FIELDS);
  return {
    new_status: requireEnum(input.new_status, TRANSITIONABLE_STATUSES, "new_status"),
    reason: optionalNullableString(input.reason, "reason"),
  };
}

// --- Source block (takedown) ----------------------------------------------

const SOURCE_BLOCK_FIELDS = ["reason"] as const;

export function validateSourceBlockInput(raw: unknown): SourceBlockInput {
  const input = assertRecord(raw);
  assertNoForbiddenKeys(input, SOURCE_BLOCK_FIELDS);
  return { reason: requireNonBlankString(input.reason, "reason") };
}

// --- Generic review decision ----------------------------------------------

const REVIEW_DECISION_FIELDS = ["status", "decision_reason"] as const;

export function validateReviewDecisionInput(raw: unknown): ReviewDecisionInput {
  const input = assertRecord(raw);
  assertNoForbiddenKeys(input, REVIEW_DECISION_FIELDS);
  return {
    status: requireEnum(input.status, REVIEW_ITEM_STATUSES, "status"),
    decision_reason: optionalNullableString(input.decision_reason, "decision_reason"),
  };
}

// --- Rights review decision -------------------------------------------------

const RIGHTS_REVIEW_DECISION_FIELDS = [
  "rights_status",
  "access_policy",
  "decision_reason",
  "tdm_opt_out_status",
  "licence_name",
  "licence_url",
] as const;

export function validateRightsReviewDecisionInput(raw: unknown): RightsReviewDecisionInput {
  const input = assertRecord(raw);
  assertNoForbiddenKeys(input, RIGHTS_REVIEW_DECISION_FIELDS);
  return {
    rights_status: requireEnum(input.rights_status, RIGHTS_STATUSES, "rights_status"),
    access_policy: requireEnum(input.access_policy, ACCESS_POLICIES, "access_policy"),
    decision_reason: requireNonBlankString(input.decision_reason, "decision_reason"),
    tdm_opt_out_status: optionalNullableEnum(input.tdm_opt_out_status, TDM_OPT_OUT_STATUSES, "tdm_opt_out_status"),
    licence_name: optionalNullableString(input.licence_name, "licence_name"),
    licence_url: optionalNullableString(input.licence_url, "licence_url"),
  };
}
