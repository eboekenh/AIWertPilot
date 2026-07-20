import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ReviewDecisionForm } from "@/components/review/ReviewDecisionForm";
import { makeReviewItem } from "@/test/fixtures";

vi.mock("@/lib/api/actions", () => ({
  decideReviewItem: vi.fn(),
}));

describe("ReviewDecisionForm", () => {
  it("excludes 'approved' as an option for a rights_review item", () => {
    render(<ReviewDecisionForm reviewItem={makeReviewItem({ review_type: "rights_review" })} />);

    const select = screen.getByLabelText("Entscheidung") as HTMLSelectElement;
    const values = within(select)
      .getAllByRole("option")
      .map((option) => (option as HTMLOptionElement).value);

    expect(values).not.toContain("approved");
  });

  it("includes 'approved' as an option for a content_review item", () => {
    render(<ReviewDecisionForm reviewItem={makeReviewItem({ review_type: "content_review" })} />);

    const select = screen.getByLabelText("Entscheidung") as HTMLSelectElement;
    const values = within(select)
      .getAllByRole("option")
      .map((option) => (option as HTMLOptionElement).value);

    expect(values).toContain("approved");
  });
});
