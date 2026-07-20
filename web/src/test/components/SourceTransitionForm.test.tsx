import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SourceTransitionForm } from "@/components/sources/SourceTransitionForm";
import { makeSource } from "@/test/fixtures";

vi.mock("@/lib/api/actions", () => ({
  transitionSource: vi.fn(),
}));

describe("SourceTransitionForm", () => {
  it("never offers 'blocked' as a transition target", () => {
    render(<SourceTransitionForm source={makeSource({ status: "registered" })} />);

    const select = screen.getByLabelText("Neuer Status") as HTMLSelectElement;
    const optionValues = within(select)
      .getAllByRole("option")
      .map((option) => (option as HTMLOptionElement).value);

    expect(optionValues).not.toContain("blocked");
  });

  it("does not offer the source's current status as a target", () => {
    render(<SourceTransitionForm source={makeSource({ status: "fetched" })} />);

    const select = screen.getByLabelText("Neuer Status") as HTMLSelectElement;
    const optionValues = within(select)
      .getAllByRole("option")
      .map((option) => (option as HTMLOptionElement).value);

    expect(optionValues).not.toContain("fetched");
    expect(optionValues.length).toBeGreaterThan(0);
  });
});
