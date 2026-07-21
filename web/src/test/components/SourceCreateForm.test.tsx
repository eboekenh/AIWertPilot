import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SourceCreateForm } from "@/components/sources/SourceCreateForm";
import { makeSource } from "@/test/fixtures";

const createSource = vi.fn();
vi.mock("@/lib/api/actions", () => ({
  createSource: (...args: unknown[]) => createSource(...args),
}));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const FORBIDDEN_FIELDS = ["status", "rights_status", "access_policy"];

describe("SourceCreateForm", () => {
  it("never renders inputs for status, rights_status, or access_policy", () => {
    render(<SourceCreateForm />);
    for (const field of FORBIDDEN_FIELDS) {
      expect(document.querySelector(`[name="${field}"]`)).toBeNull();
    }
  });

  it("submits a payload that never contains status, rights_status, or access_policy", async () => {
    const user = userEvent.setup();
    createSource.mockResolvedValue({ ok: true, data: makeSource({ title: "Neue Quelle" }) });
    render(<SourceCreateForm />);

    await user.type(screen.getByLabelText(/Quellenschlüssel/), "NEW_SOURCE");
    await user.type(screen.getByLabelText("Titel"), "Neue Quelle");
    await user.type(screen.getByLabelText(/Verlag/), "Verlag GmbH");
    await user.type(screen.getByLabelText("URL"), "https://example.com/new");
    await user.type(screen.getByLabelText("Quellentyp"), "official_statistics");
    await user.click(screen.getByRole("button", { name: "Quelle registrieren" }));

    expect(createSource).toHaveBeenCalledTimes(1);
    const payload = createSource.mock.calls[0][0] as Record<string, unknown>;
    for (const field of FORBIDDEN_FIELDS) {
      expect(payload).not.toHaveProperty(field);
    }
    expect(payload.source_key).toBe("NEW_SOURCE");
    expect(payload.title).toBe("Neue Quelle");
  });

  it("returns to an empty form when 'Weitere Quelle anlegen' is clicked after a successful create", async () => {
    const user = userEvent.setup();
    createSource.mockResolvedValue({ ok: true, data: makeSource({ title: "Neue Quelle" }) });
    render(<SourceCreateForm />);

    await user.type(screen.getByLabelText(/Quellenschlüssel/), "NEW_SOURCE");
    await user.type(screen.getByLabelText("Titel"), "Neue Quelle");
    await user.type(screen.getByLabelText(/Verlag/), "Verlag GmbH");
    await user.type(screen.getByLabelText("URL"), "https://example.com/new");
    await user.type(screen.getByLabelText("Quellentyp"), "official_statistics");
    await user.click(screen.getByRole("button", { name: "Quelle registrieren" }));

    expect(await screen.findByText(/wurde registriert/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Weitere Quelle anlegen" }));

    // The success view must be gone and a genuinely empty form must be back.
    expect(screen.queryByText(/wurde registriert/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Quelle registrieren" })).toBeInTheDocument();
    expect(screen.getByLabelText(/Quellenschlüssel/)).toHaveValue("");
    expect(screen.getByLabelText("Titel")).toHaveValue("");
  });
});
