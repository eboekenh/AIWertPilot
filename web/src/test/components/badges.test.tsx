import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AccessPolicyBadge } from "@/components/badges/AccessPolicyBadge";
import { FreshnessBadge } from "@/components/badges/FreshnessBadge";
import { RightsBadge } from "@/components/badges/RightsBadge";
import { StatusBadge } from "@/components/badges/StatusBadge";

describe("StatusBadge", () => {
  it("renders the German label for a known status", () => {
    render(<StatusBadge status="published" />);
    expect(screen.getByText("Veröffentlicht")).toBeInTheDocument();
  });

  it("falls back to the raw value for an unrecognized status", () => {
    render(<StatusBadge status="totally_unknown_status" />);
    expect(screen.getByText("totally_unknown_status")).toBeInTheDocument();
  });
});

describe("RightsBadge", () => {
  it("renders the German label for a known rights status", () => {
    render(<RightsBadge rightsStatus="needs_review" />);
    expect(screen.getByText("Prüfung erforderlich")).toBeInTheDocument();
  });
});

describe("AccessPolicyBadge", () => {
  it("renders the German label for a known access policy", () => {
    render(<AccessPolicyBadge accessPolicy="blocked" />);
    expect(screen.getByText("Gesperrt")).toBeInTheDocument();
  });
});

describe("FreshnessBadge", () => {
  it("renders the German label for a known freshness state", () => {
    render(<FreshnessBadge freshnessState="stale" />);
    expect(screen.getByText("Veraltet")).toBeInTheDocument();
  });
});
