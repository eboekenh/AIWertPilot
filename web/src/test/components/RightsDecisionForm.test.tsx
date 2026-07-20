import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RightsDecisionForm } from "@/components/review/RightsDecisionForm";
import { makeReviewItem } from "@/test/fixtures";

const resolveRightsReview = vi.fn();
vi.mock("@/lib/api/actions", () => ({
  resolveRightsReview: (...args: unknown[]) => resolveRightsReview(...args),
}));

describe("RightsDecisionForm", () => {
  it("marks decision_reason as a required field", () => {
    render(<RightsDecisionForm reviewItem={makeReviewItem({ review_type: "rights_review" })} />);
    expect(screen.getByLabelText(/Begründung \(erforderlich\)/)).toBeRequired();
  });

  it("displays a backend validation error returned by the action, without crashing", async () => {
    const user = userEvent.setup();
    resolveRightsReview.mockResolvedValue({
      ok: false,
      error: {
        code: "validation_failed",
        message: "access_policy 'blocked' is not permitted for rights_status 'reviewed_allowed'",
        details: {},
      },
    });
    render(<RightsDecisionForm reviewItem={makeReviewItem({ review_type: "rights_review" })} />);

    await user.selectOptions(screen.getByLabelText("Rechtestatus"), "reviewed_allowed");
    await user.selectOptions(screen.getByLabelText("Zugriffsrichtlinie"), "blocked");
    await user.type(screen.getByLabelText(/Begründung \(erforderlich\)/), "Testbegründung");
    await user.click(screen.getByRole("button", { name: "Rechteentscheidung speichern" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/not permitted for rights_status/);
  });
});
