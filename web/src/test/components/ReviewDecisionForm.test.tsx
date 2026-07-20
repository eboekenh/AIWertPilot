import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ReviewDecisionForm } from "@/components/review/ReviewDecisionForm";
import { makeReviewItem } from "@/test/fixtures";

vi.mock("@/lib/api/actions", () => ({
  decideReviewItem: vi.fn(),
}));

function optionValuesFor(overrides: Parameters<typeof makeReviewItem>[0]): string[] {
  render(<ReviewDecisionForm reviewItem={makeReviewItem(overrides)} />);
  const select = screen.getByLabelText("Entscheidung") as HTMLSelectElement;
  return within(select)
    .getAllByRole("option")
    .map((option) => (option as HTMLOptionElement).value);
}

describe("ReviewDecisionForm", () => {
  it("excludes 'approved' as an option for an open rights_review item", () => {
    const values = optionValuesFor({ review_type: "rights_review", status: "open" });
    expect(values).not.toContain("approved");
    expect(values.sort()).toEqual(["cancelled", "in_progress", "needs_changes", "rejected"].sort());
  });

  it("includes 'approved' as an option for an open content_review item", () => {
    const values = optionValuesFor({ review_type: "content_review", status: "open" });
    expect(values).toContain("approved");
    expect(values.sort()).toEqual(["approved", "cancelled", "in_progress", "needs_changes", "rejected"].sort());
  });

  it("only offers the backend's legal transitions from 'needs_changes' (and never the current status itself)", () => {
    const values = optionValuesFor({ review_type: "content_review", status: "needs_changes" });
    expect(values.sort()).toEqual(["approved", "cancelled", "in_progress", "rejected"].sort());
    expect(values).not.toContain("needs_changes");
  });

  it("shows an explanatory message instead of an empty dropdown for a terminal status", () => {
    render(<ReviewDecisionForm reviewItem={makeReviewItem({ review_type: "content_review", status: "approved" })} />);
    expect(screen.queryByLabelText("Entscheidung")).not.toBeInTheDocument();
    expect(screen.getByText(/keine weiteren Entscheidungen möglich/)).toBeInTheDocument();
  });
});
