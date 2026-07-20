import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ActionError } from "@/components/ui/ActionError";

describe("ActionError", () => {
  it("renders the backend's top-level error message", () => {
    render(<ActionError error={{ code: "validation_failed", message: "Validierung fehlgeschlagen", details: {} }} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Validierung fehlgeschlagen");
  });

  it("lists per-field validation errors from FastAPI's RequestValidationError shape", () => {
    render(
      <ActionError
        error={{
          code: "validation_failed",
          message: "request validation failed",
          details: {
            errors: [
              { loc: ["body", "original_url"], msg: "Field required" },
              { loc: ["body", "tier"], msg: "Input should be A, B, C, D or E" },
            ],
          },
        }}
      />,
    );

    expect(screen.getByText(/body.original_url: Field required/)).toBeInTheDocument();
    expect(screen.getByText(/body.tier: Input should be A, B, C, D or E/)).toBeInTheDocument();
  });

  it("renders no list when details has no errors array", () => {
    render(<ActionError error={{ code: "duplicate_source", message: "Quelle existiert bereits", details: {} }} />);
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
  });
});
