import { afterEach, describe, expect, it } from "vitest";

import { DevWritesConfigError, getApiBaseUrl, isDevWritesEnabled, resolveDevApiKey } from "@/lib/api/config";

const ORIGINAL_ENV = { ...process.env };

describe("isDevWritesEnabled", () => {
  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
  });

  it("defaults to false when the env var is unset", () => {
    delete process.env.ENABLE_DEV_WRITES;
    expect(isDevWritesEnabled()).toBe(false);
  });

  it("is false for any value other than the exact string 'true'", () => {
    process.env.ENABLE_DEV_WRITES = "1";
    expect(isDevWritesEnabled()).toBe(false);
    process.env.ENABLE_DEV_WRITES = "TRUE";
    expect(isDevWritesEnabled()).toBe(false);
    process.env.ENABLE_DEV_WRITES = "yes";
    expect(isDevWritesEnabled()).toBe(false);
  });

  it("is true only when explicitly set to 'true'", () => {
    process.env.ENABLE_DEV_WRITES = "true";
    expect(isDevWritesEnabled()).toBe(true);
  });

  it("is not read from the NEXT_PUBLIC_ prefixed variable — that would bundle it into the browser", () => {
    delete process.env.ENABLE_DEV_WRITES;
    process.env.NEXT_PUBLIC_ENABLE_DEV_WRITES = "true";
    expect(isDevWritesEnabled()).toBe(false);
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

describe("resolveDevApiKey", () => {
  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
  });

  it("throws DevWritesConfigError when DEV_API_KEY is unset", () => {
    delete process.env.DEV_API_KEY;
    expect(() => resolveDevApiKey()).toThrow(DevWritesConfigError);
  });

  it("throws when DEV_API_KEY is blank or whitespace-only", () => {
    process.env.DEV_API_KEY = "   ";
    expect(() => resolveDevApiKey()).toThrow(DevWritesConfigError);
  });

  it("throws when DEV_API_KEY is still the shipped placeholder", () => {
    process.env.DEV_API_KEY = "change-me-dev-key";
    expect(() => resolveDevApiKey()).toThrow(DevWritesConfigError);
  });

  it("returns the trimmed key when a real value is configured", () => {
    process.env.DEV_API_KEY = "  a-real-local-dev-key  ";
    expect(resolveDevApiKey()).toBe("a-real-local-dev-key");
  });
});
