import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RightsDecisionForm } from "@/components/review/RightsDecisionForm";
import { makeReviewItem } from "@/test/fixtures";

const resolveRightsReview = vi.fn();
vi.mock("@/lib/api/actions", () => ({
  resolveRightsReview: (...args: unknown[]) => resolveRightsReview(...args),
}));

function accessPolicyOptionValues(): string[] {
  const select = screen.getByLabelText("Zugriffsrichtlinie") as HTMLSelectElement;
  return within(select)
    .getAllByRole("option")
    .map((option) => (option as HTMLOptionElement).value);
}

describe("RightsDecisionForm", () => {
  it("marks decision_reason as a required field", () => {
    render(<RightsDecisionForm reviewItem={makeReviewItem({ review_type: "rights_review" })} />);
    expect(screen.getByLabelText(/Begründung \(erforderlich\)/)).toBeRequired();
  });

  it("never offers 'needs_review' as a rights_status outcome", () => {
    render(<RightsDecisionForm reviewItem={makeReviewItem({ review_type: "rights_review" })} />);
    const select = screen.getByLabelText("Rechtestatus") as HTMLSelectElement;
    const values = within(select)
      .getAllByRole("option")
      .map((option) => (option as HTMLOptionElement).value);
    expect(values).not.toContain("needs_review");
    expect(values.sort()).toEqual(["blocked", "reviewed_allowed", "reviewed_restricted"].sort());
  });

  it("starts with a valid rights_status/access_policy pair selected by default", () => {
    render(<RightsDecisionForm reviewItem={makeReviewItem({ review_type: "rights_review" })} />);
    expect(screen.getByLabelText("Rechtestatus")).toHaveValue("reviewed_allowed");
    expect(screen.getByLabelText("Zugriffsrichtlinie")).toHaveValue("metadata_only");
  });

  it("restricts access_policy to ['blocked'] and auto-selects it when rights_status is set to 'blocked'", async () => {
    const user = userEvent.setup();
    render(<RightsDecisionForm reviewItem={makeReviewItem({ review_type: "rights_review" })} />);

    await user.selectOptions(screen.getByLabelText("Rechtestatus"), "blocked");

    expect(accessPolicyOptionValues()).toEqual(["blocked"]);
    expect(screen.getByLabelText("Zugriffsrichtlinie")).toHaveValue("blocked");
  });

  it("excludes 'full_text_allowed' from access_policy when rights_status is 'reviewed_restricted'", async () => {
    const user = userEvent.setup();
    render(<RightsDecisionForm reviewItem={makeReviewItem({ review_type: "rights_review" })} />);

    await user.selectOptions(screen.getByLabelText("Rechtestatus"), "reviewed_restricted");

    const values = accessPolicyOptionValues();
    expect(values).not.toContain("full_text_allowed");
    expect(values.sort()).toEqual(["metadata_only", "short_evidence"].sort());
  });

  it("re-narrowing back to 'reviewed_allowed' restores the full access_policy option set", async () => {
    const user = userEvent.setup();
    render(<RightsDecisionForm reviewItem={makeReviewItem({ review_type: "rights_review" })} />);

    await user.selectOptions(screen.getByLabelText("Rechtestatus"), "blocked");
    await user.selectOptions(screen.getByLabelText("Rechtestatus"), "reviewed_allowed");

    expect(accessPolicyOptionValues().sort()).toEqual(
      ["metadata_only", "short_evidence", "full_text_allowed"].sort(),
    );
  });

  it("displays a backend validation error returned by the action, without crashing", async () => {
    const user = userEvent.setup();
    resolveRightsReview.mockResolvedValue({
      ok: false,
      error: {
        code: "invalid_state_transition",
        message: "review_item ...: cannot transition from approved to approved",
        details: {},
      },
    });
    render(<RightsDecisionForm reviewItem={makeReviewItem({ review_type: "rights_review" })} />);

    // A perfectly valid, selectable combination — the backend can still
    // reject the request for other reasons (e.g. the item is no longer
    // open), and that must still surface cleanly.
    await user.type(screen.getByLabelText(/Begründung \(erforderlich\)/), "Testbegründung");
    await user.click(screen.getByRole("button", { name: "Rechteentscheidung speichern" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/cannot transition from approved to approved/);
  });
});
