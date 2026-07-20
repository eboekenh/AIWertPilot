import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";

describe("LoadingState", () => {
  it("renders a status role with the loading label", () => {
    render(<LoadingState />);
    expect(screen.getByRole("status")).toHaveTextContent("Wird geladen");
  });

  it("accepts a custom label", () => {
    render(<LoadingState label="Quellen werden geladen…" />);
    expect(screen.getByRole("status")).toHaveTextContent("Quellen werden geladen");
  });
});

describe("EmptyState", () => {
  it("renders the title and description", () => {
    render(<EmptyState title="Keine Quellen gefunden" description="Passen Sie die Filter an." />);
    expect(screen.getByText("Keine Quellen gefunden")).toBeInTheDocument();
    expect(screen.getByText("Passen Sie die Filter an.")).toBeInTheDocument();
  });
});

describe("ErrorState", () => {
  it("renders an alert role with the safe user-facing message", () => {
    render(<ErrorState message="Der Server ist nicht erreichbar." />);
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Der Server ist nicht erreichbar.");
  });

  it("never requires a raw exception to render — message is plain text", () => {
    render(<ErrorState message="Unerwarteter Serverfehler (Status 500)." />);
    expect(screen.getByRole("alert")).toHaveTextContent("Unerwarteter Serverfehler (Status 500).");
  });
});
