import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SourceTransitionForm } from "@/components/sources/SourceTransitionForm";
import { makeSource } from "@/test/fixtures";

vi.mock("@/lib/api/actions", () => ({
  transitionSource: vi.fn(),
}));

function optionValuesFor(status: string): string[] {
  render(<SourceTransitionForm source={makeSource({ status })} />);
  const select = screen.getByLabelText("Neuer Status") as HTMLSelectElement;
  return within(select)
    .getAllByRole("option")
    .map((option) => (option as HTMLOptionElement).value);
}

describe("SourceTransitionForm", () => {
  it("never offers 'blocked' as a transition target", () => {
    expect(optionValuesFor("registered")).not.toContain("blocked");
  });

  it("does not offer the source's current status as a target", () => {
    const values = optionValuesFor("fetched");
    expect(values).not.toContain("fetched");
    expect(values.length).toBeGreaterThan(0);
  });

  it("offers exactly the backend's SOURCE_STATUS_TRANSITIONS targets for 'registered' (minus blocked)", () => {
    const values = optionValuesFor("registered");
    expect(values.sort()).toEqual(["archived", "fetched", "rejected", "superseded"].sort());
  });

  it("offers exactly the backend's SOURCE_STATUS_TRANSITIONS targets for 'under_review' (minus blocked)", () => {
    const values = optionValuesFor("under_review");
    expect(values.sort()).toEqual(["approved", "rejected", "superseded"].sort());
  });

  it("offers exactly the backend's SOURCE_STATUS_TRANSITIONS targets for 'approved' (minus blocked)", () => {
    const values = optionValuesFor("approved");
    expect(values.sort()).toEqual(["published", "superseded"].sort());
  });

  it("shows an explanatory message instead of an empty dropdown for a terminal status", () => {
    render(<SourceTransitionForm source={makeSource({ status: "archived" })} />);
    expect(screen.queryByLabelText("Neuer Status")).not.toBeInTheDocument();
    expect(screen.getByText(/keine weiteren Statusübergänge möglich/)).toBeInTheDocument();
  });
});
