import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/client";
import { DevWritesConfigError } from "@/lib/api/config";

const apiFetchMock = vi.fn();
vi.mock("@/lib/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/client")>("@/lib/api/client");
  return {
    ...actual,
    apiFetch: (...args: unknown[]) => apiFetchMock(...args),
  };
});

const isDevWritesEnabledMock = vi.fn();
const resolveDevApiKeyMock = vi.fn();
vi.mock("@/lib/api/config", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/config")>("@/lib/api/config");
  return {
    ...actual,
    isDevWritesEnabled: () => isDevWritesEnabledMock(),
    resolveDevApiKey: () => resolveDevApiKeyMock(),
    getApiBaseUrl: () => "http://backend.test",
  };
});

vi.mock("next/cache", () => ({
  revalidatePath: vi.fn(),
}));

// Imported after the mocks above so actions.ts picks up the mocked deps.
const { createSource, transitionSource, blockSource, decideReviewItem, resolveRightsReview } = await import(
  "@/lib/api/actions"
);

const VALID_SOURCE_CREATE = {
  source_key: "TEST_SOURCE",
  title: "Test Source",
  publisher: "Test Publisher",
  original_url: "https://example.com/report",
  source_type: "official_statistics",
  tier: "A" as const,
};

beforeEach(() => {
  apiFetchMock.mockReset();
  isDevWritesEnabledMock.mockReset();
  resolveDevApiKeyMock.mockReset();
  isDevWritesEnabledMock.mockReturnValue(true);
  resolveDevApiKeyMock.mockReturnValue("a-real-dev-key");
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("write actions — disabled writes", () => {
  it("rejects without calling the backend when dev writes are disabled", async () => {
    isDevWritesEnabledMock.mockReturnValue(false);

    const result = await createSource(VALID_SOURCE_CREATE);

    expect(result).toEqual({
      ok: false,
      error: expect.objectContaining({ code: "dev_writes_disabled" }),
    });
    expect(apiFetchMock).not.toHaveBeenCalled();
    expect(resolveDevApiKeyMock).not.toHaveBeenCalled();
  });
});

describe("write actions — missing/placeholder API key", () => {
  it("fails closed with a configuration error and never calls the backend", async () => {
    resolveDevApiKeyMock.mockImplementation(() => {
      throw new DevWritesConfigError("DEV_API_KEY ist nicht gesetzt.");
    });

    const result = await createSource(VALID_SOURCE_CREATE);

    expect(result).toEqual({
      ok: false,
      error: expect.objectContaining({ code: "configuration_error" }),
    });
    expect(apiFetchMock).not.toHaveBeenCalled();
  });
});

describe("write actions — malformed inputs", () => {
  it("rejects a missing required field without calling the backend", async () => {
    const missingTitle: Record<string, unknown> = { ...VALID_SOURCE_CREATE };
    delete missingTitle.title;
    const result = await createSource(missingTitle as unknown as typeof VALID_SOURCE_CREATE);

    expect(result).toEqual({
      ok: false,
      error: expect.objectContaining({ code: "validation_failed" }),
    });
    expect(apiFetchMock).not.toHaveBeenCalled();
  });

  it("rejects a wrong-typed field without calling the backend", async () => {
    const result = await createSource({
      ...VALID_SOURCE_CREATE,
      refresh_interval_days: "ninety" as unknown as number,
    });

    expect(result.ok).toBe(false);
    expect(apiFetchMock).not.toHaveBeenCalled();
  });

  it("rejects a non-object payload without calling the backend", async () => {
    const result = await createSource("not-an-object" as unknown as typeof VALID_SOURCE_CREATE);
    expect(result.ok).toBe(false);
    expect(apiFetchMock).not.toHaveBeenCalled();
  });
});

describe("write actions — forbidden fields", () => {
  it("rejects status/rights_status/access_policy smuggled into a create payload", async () => {
    const result = await createSource({
      ...VALID_SOURCE_CREATE,
      status: "published",
      rights_status: "reviewed_allowed",
      access_policy: "full_text_allowed",
    } as unknown as typeof VALID_SOURCE_CREATE);

    expect(result).toEqual({
      ok: false,
      error: expect.objectContaining({ code: "validation_failed" }),
    });
    expect(apiFetchMock).not.toHaveBeenCalled();
  });
});

describe("write actions — blocked-through-transition attempts", () => {
  it("rejects new_status='blocked' locally, never reaching the backend", async () => {
    const result = await transitionSource("source-1", {
      new_status: "blocked" as never,
    });

    expect(result).toEqual({
      ok: false,
      error: expect.objectContaining({ code: "validation_failed" }),
    });
    expect(apiFetchMock).not.toHaveBeenCalled();
  });
});

describe("write actions — blank block reasons", () => {
  it("rejects a whitespace-only reason locally, never reaching the backend", async () => {
    const result = await blockSource("source-1", { reason: "   " });

    expect(result).toEqual({
      ok: false,
      error: expect.objectContaining({ code: "validation_failed" }),
    });
    expect(apiFetchMock).not.toHaveBeenCalled();
  });

  it("rejects a missing reason locally, never reaching the backend", async () => {
    const result = await blockSource("source-1", {} as unknown as { reason: string });
    expect(result.ok).toBe(false);
    expect(apiFetchMock).not.toHaveBeenCalled();
  });
});

describe("write actions — happy path", () => {
  it("forwards a validated, reconstructed payload with the resolved API key", async () => {
    apiFetchMock.mockResolvedValue({ id: "new-id", title: "Test Source" });

    const result = await createSource(VALID_SOURCE_CREATE);

    expect(result.ok).toBe(true);
    expect(apiFetchMock).toHaveBeenCalledWith(
      "http://backend.test",
      "/api/v1/sources",
      expect.objectContaining({
        method: "POST",
        headers: { "X-API-Key": "a-real-dev-key" },
        body: expect.objectContaining({ source_key: "TEST_SOURCE", title: "Test Source" }),
      }),
    );
  });

  it("surfaces a backend ApiError as a validation_failed-shaped ActionResult", async () => {
    apiFetchMock.mockRejectedValue(new ApiError(422, "validation_failed", "backend says no", { errors: [] }));

    const result = await createSource(VALID_SOURCE_CREATE);

    expect(result).toEqual({
      ok: false,
      error: { code: "validation_failed", message: "backend says no", details: { errors: [] } },
    });
  });
});

describe("decideReviewItem / resolveRightsReview — malformed inputs", () => {
  it("rejects an unknown review status locally", async () => {
    const result = await decideReviewItem("item-1", { status: "not_a_real_status" as never });
    expect(result.ok).toBe(false);
    expect(apiFetchMock).not.toHaveBeenCalled();
  });

  it("rejects a blank decision_reason for a rights decision locally", async () => {
    const result = await resolveRightsReview("item-1", {
      rights_status: "reviewed_allowed",
      access_policy: "short_evidence",
      decision_reason: "   ",
    });
    expect(result.ok).toBe(false);
    expect(apiFetchMock).not.toHaveBeenCalled();
  });

  it("rejects an unrecognized access_policy value locally", async () => {
    const result = await resolveRightsReview("item-1", {
      rights_status: "reviewed_allowed",
      access_policy: "not_a_real_policy" as never,
      decision_reason: "valid reason",
    });
    expect(result.ok).toBe(false);
    expect(apiFetchMock).not.toHaveBeenCalled();
  });
});
