import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch, buildQueryString } from "@/lib/api/client";

function jsonResponse(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
    ...init,
  });
}

describe("apiFetch", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns parsed JSON on a 2xx response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ status: "ok" })),
    );

    const result = await apiFetch<{ status: string }>("http://backend", "/health");
    expect(result).toEqual({ status: "ok" });
  });

  it("throws ApiError with the backend's code/message/details on a non-2xx response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          { error: { code: "not_found", message: "source nicht gefunden", details: { id: "abc" } } },
          { status: 404 },
        ),
      ),
    );

    await expect(apiFetch("http://backend", "/api/v1/sources/abc")).rejects.toMatchObject({
      status: 404,
      code: "not_found",
      message: "source nicht gefunden",
      details: { id: "abc" },
    });
  });

  it("throws a generic ApiError when a non-2xx response has no error envelope", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("<html>gateway error</html>", { status: 502 })),
    );

    await expect(apiFetch("http://backend", "/health")).rejects.toMatchObject({
      status: 502,
      code: "unknown_error",
    });
  });

  it("throws a network_error ApiError when fetch itself rejects", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("fetch failed")),
    );

    await expect(apiFetch("http://backend", "/health")).rejects.toMatchObject({
      status: 0,
      code: "network_error",
    });
  });

  it("sends the request body as JSON with a Content-Type header when provided", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch("http://backend", "/api/v1/sources", {
      method: "POST",
      body: { title: "Test" },
    });

    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ title: "Test" }));
    expect(init.headers["Content-Type"]).toBe("application/json");
  });

  it("is an instance of ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ error: { code: "x", message: "y", details: {} } }, { status: 400 })),
    );
    try {
      await apiFetch("http://backend", "/x");
      expect.unreachable("should have thrown");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
    }
  });
});

describe("buildQueryString", () => {
  it("returns an empty string when no params are set", () => {
    expect(buildQueryString({})).toBe("");
    expect(buildQueryString({ status: undefined, limit: undefined })).toBe("");
  });

  it("omits empty-string values but keeps zero", () => {
    expect(buildQueryString({ status: "", offset: 0 })).toBe("?offset=0");
  });

  it("builds a query string from multiple params", () => {
    const qs = buildQueryString({ status: "registered", limit: 20 });
    const params = new URLSearchParams(qs.slice(1));
    expect(params.get("status")).toBe("registered");
    expect(params.get("limit")).toBe("20");
  });
});
