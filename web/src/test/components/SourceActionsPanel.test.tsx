import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SourceActionsPanel } from "@/components/sources/SourceActionsPanel";
import { makeSource } from "@/test/fixtures";

// actions.ts is a "use server" file — outside a real Next.js build its
// exports are plain async functions that would otherwise try to hit a real
// backend. Mocked here so these are pure component-behavior tests.
vi.mock("@/lib/api/actions", () => ({
  transitionSource: vi.fn(),
  blockSource: vi.fn(),
}));

describe("SourceActionsPanel dev-write gating", () => {
  it("hides write controls and shows the dev-writes notice when devWritesEnabled is false", () => {
    render(<SourceActionsPanel source={makeSource()} devWritesEnabled={false} />);

    expect(screen.queryByRole("button", { name: "Quelle sperren" })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Neuer Status")).not.toBeInTheDocument();
    expect(screen.getByText(/Schreibaktionen sind deaktiviert/)).toBeInTheDocument();
  });

  it("shows write controls when devWritesEnabled is explicitly true", () => {
    render(<SourceActionsPanel source={makeSource({ status: "registered" })} devWritesEnabled />);

    expect(screen.getByRole("button", { name: "Quelle sperren" })).toBeInTheDocument();
    expect(screen.getByLabelText("Neuer Status")).toBeInTheDocument();
    expect(screen.queryByText(/Schreibaktionen sind deaktiviert/)).not.toBeInTheDocument();
  });
});
