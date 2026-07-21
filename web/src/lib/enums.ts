/**
 * German display labels and visual "tone" for every backend enum value used
 * in this app. Centralized here — the one place these mappings live — so
 * badges, filters, and forms never redefine their own copy of the value
 * set and drift apart. The value sets themselves are defined in
 * lib/api/types.ts, mirrored from src/de_ai_kb/domain/enums.py.
 */

export type Tone = "neutral" | "info" | "warning" | "success" | "danger";

interface EnumMeta {
  label: string;
  tone: Tone;
}

export const SOURCE_STATUS_META: Record<string, EnumMeta> = {
  discovered: { label: "Entdeckt", tone: "neutral" },
  registered: { label: "Registriert", tone: "info" },
  fetched: { label: "Abgerufen", tone: "info" },
  extracted: { label: "Extrahiert", tone: "info" },
  under_review: { label: "In Prüfung", tone: "warning" },
  approved: { label: "Freigegeben", tone: "success" },
  published: { label: "Veröffentlicht", tone: "success" },
  rejected: { label: "Abgelehnt", tone: "danger" },
  blocked: { label: "Gesperrt", tone: "danger" },
  superseded: { label: "Ersetzt", tone: "neutral" },
  archived: { label: "Archiviert", tone: "neutral" },
};

export const RIGHTS_STATUS_META: Record<string, EnumMeta> = {
  needs_review: { label: "Prüfung erforderlich", tone: "warning" },
  reviewed_allowed: { label: "Geprüft: erlaubt", tone: "success" },
  reviewed_restricted: { label: "Geprüft: eingeschränkt", tone: "warning" },
  blocked: { label: "Gesperrt", tone: "danger" },
};

export const ACCESS_POLICY_META: Record<string, EnumMeta> = {
  metadata_only: { label: "Nur Metadaten", tone: "neutral" },
  short_evidence: { label: "Kurzbeleg erlaubt", tone: "info" },
  full_text_allowed: { label: "Volltext erlaubt", tone: "success" },
  blocked: { label: "Gesperrt", tone: "danger" },
  unknown: { label: "Unbekannt", tone: "neutral" },
};

export const REVIEW_ITEM_STATUS_META: Record<string, EnumMeta> = {
  open: { label: "Offen", tone: "warning" },
  in_progress: { label: "In Bearbeitung", tone: "info" },
  approved: { label: "Freigegeben", tone: "success" },
  rejected: { label: "Abgelehnt", tone: "danger" },
  needs_changes: { label: "Änderungen nötig", tone: "warning" },
  cancelled: { label: "Abgebrochen", tone: "neutral" },
};

export const REVIEW_TYPE_META: Record<string, EnumMeta> = {
  rights_review: { label: "Rechteprüfung", tone: "info" },
  content_review: { label: "Inhaltsprüfung", tone: "info" },
  dedup_candidate: { label: "Dublettenkandidat", tone: "neutral" },
};

export const FRESHNESS_STATE_META: Record<string, EnumMeta> = {
  fresh: { label: "Aktuell", tone: "success" },
  due_soon: { label: "Bald fällig", tone: "warning" },
  stale: { label: "Veraltet", tone: "danger" },
  unknown: { label: "Unbekannt", tone: "neutral" },
};

export const SOURCE_TIER_LABEL: Record<string, string> = {
  A: "Tier A",
  B: "Tier B",
  C: "Tier C",
  D: "Tier D",
  E: "Tier E",
};

/** Fallback for a value not present in a meta table (defensive — the
 * backend is the source of truth, so an unrecognized value should still
 * render something instead of crashing). */
export function metaOrFallback(table: Record<string, EnumMeta>, value: string): EnumMeta {
  return table[value] ?? { label: value, tone: "neutral" };
}
