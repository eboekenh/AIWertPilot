import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SourceBlockDialog } from "@/components/sources/SourceBlockDialog";
import { makeSource } from "@/test/fixtures";

const blockSource = vi.fn();
vi.mock("@/lib/api/actions", () => ({
  blockSource: (...args: unknown[]) => blockSource(...args),
}));

describe("SourceBlockDialog", () => {
  it("requires a non-blank reason before the block action can be confirmed", async () => {
    const user = userEvent.setup();
    render(<SourceBlockDialog source={makeSource({ status: "registered" })} />);

    await user.click(screen.getByRole("button", { name: "Quelle sperren" }));

    const confirmButton = screen.getByRole("button", { name: "Sperren" });
    expect(confirmButton).toBeDisabled();

    await user.type(screen.getByLabelText(/Begründung/), "   ");
    expect(confirmButton).toBeDisabled();

    await user.type(screen.getByLabelText(/Begründung/), "Publisher hat Rechte entzogen");
    expect(confirmButton).toBeEnabled();
  });

  it("calls blockSource with the trimmed reason on confirm", async () => {
    const user = userEvent.setup();
    blockSource.mockResolvedValue({ ok: true, data: makeSource({ status: "blocked" }) });
    render(<SourceBlockDialog source={makeSource({ id: "src-1", status: "registered" })} />);

    await user.click(screen.getByRole("button", { name: "Quelle sperren" }));
    await user.type(screen.getByLabelText(/Begründung/), "  Takedown-Anfrage  ");
    await user.click(screen.getByRole("button", { name: "Sperren" }));

    expect(blockSource).toHaveBeenCalledWith("src-1", { reason: "Takedown-Anfrage" });
  });

  it("shows a note instead of the button when the source is already blocked", () => {
    render(<SourceBlockDialog source={makeSource({ status: "blocked" })} />);
    expect(screen.getByText(/bereits gesperrt/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Quelle sperren" })).not.toBeInTheDocument();
  });
});
