import { afterEach, describe, expect, it } from "vitest";

import { getApiBaseUrl, isDevWritesEnabled } from "@/lib/api/config";

const ORIGINAL_ENV = { ...process.env };

describe("isDevWritesEnabled", () => {
  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
  });

  it("defaults to false when the env var is unset", () => {
    delete process.env.NEXT_PUBLIC_ENABLE_DEV_WRITES;
    expect(isDevWritesEnabled()).toBe(false);
  });

  it("is false for any value other than the exact string 'true'", () => {
    process.env.NEXT_PUBLIC_ENABLE_DEV_WRITES = "1";
    expect(isDevWritesEnabled()).toBe(false);
    process.env.NEXT_PUBLIC_ENABLE_DEV_WRITES = "TRUE";
    expect(isDevWritesEnabled()).toBe(false);
    process.env.NEXT_PUBLIC_ENABLE_DEV_WRITES = "yes";
    expect(isDevWritesEnabled()).toBe(false);
  });

  it("is true only when explicitly set to 'true'", () => {
    process.env.NEXT_PUBLIC_ENABLE_DEV_WRITES = "true";
    expect(isDevWritesEnabled()).toBe(true);
  });
});

describe("getApiBaseUrl", () => {
  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
  });

  it("falls back to the local backend default when unset", () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    expect(getApiBaseUrl()).toBe("http://localhost:8000");
  });

  it("uses the configured URL and strips a trailing slash", () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.example.com/";
    expect(getApiBaseUrl()).toBe("https://api.example.com");
  });
});
