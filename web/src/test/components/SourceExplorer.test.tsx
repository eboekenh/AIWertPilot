import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { SourceExplorer } from "@/components/sources/SourceExplorer";
import { makeSource } from "@/test/fixtures";

const sources = [
  makeSource({
    id: "1",
    title: "Destatis KI-Nutzung",
    source_key: "DESTATIS_AI",
    publisher: "Destatis",
    status: "registered",
    rights_status: "needs_review",
    access_policy: "metadata_only",
    source_type: "official_statistics",
  }),
  makeSource({
    id: "2",
    title: "Bitkom KI-Studie",
    source_key: "BITKOM_AI",
    publisher: "Bitkom",
    status: "published",
    rights_status: "reviewed_allowed",
    access_policy: "short_evidence",
    source_type: "industry_report",
  }),
  makeSource({
    id: "3",
    title: "Gesperrte Quelle",
    source_key: "BLOCKED_ONE",
    publisher: "Bitkom",
    status: "blocked",
    rights_status: "blocked",
    access_policy: "blocked",
    source_type: "industry_report",
  }),
];

describe("SourceExplorer", () => {
  it("renders all sources initially", () => {
    render(<SourceExplorer sources={sources} />);
    expect(screen.getByText("Destatis KI-Nutzung")).toBeInTheDocument();
    expect(screen.getByText("Bitkom KI-Studie")).toBeInTheDocument();
    expect(screen.getByText("Gesperrte Quelle")).toBeInTheDocument();
    expect(screen.getByText("3 von 3 Quellen")).toBeInTheDocument();
  });

  it("filters by free-text search across title/key/publisher", async () => {
    const user = userEvent.setup();
    render(<SourceExplorer sources={sources} />);

    await user.type(screen.getByLabelText("Suche"), "Destatis");

    expect(screen.getByText("Destatis KI-Nutzung")).toBeInTheDocument();
    expect(screen.queryByText("Bitkom KI-Studie")).not.toBeInTheDocument();
    expect(screen.getByText("1 von 3 Quellen")).toBeInTheDocument();
  });

  it("filters by lifecycle status", async () => {
    const user = userEvent.setup();
    render(<SourceExplorer sources={sources} />);

    await user.selectOptions(screen.getByLabelText("Status"), "published");

    expect(screen.getByText("Bitkom KI-Studie")).toBeInTheDocument();
    expect(screen.queryByText("Destatis KI-Nutzung")).not.toBeInTheDocument();
  });

  it("filters by rights status (client-side, since the backend has no such query param)", async () => {
    const user = userEvent.setup();
    render(<SourceExplorer sources={sources} />);

    await user.selectOptions(screen.getByLabelText("Rechtestatus"), "blocked");

    expect(screen.getByText("Gesperrte Quelle")).toBeInTheDocument();
    expect(screen.queryByText("Destatis KI-Nutzung")).not.toBeInTheDocument();
  });

  it("filters by access policy", async () => {
    const user = userEvent.setup();
    render(<SourceExplorer sources={sources} />);

    await user.selectOptions(screen.getByLabelText("Zugriffsrichtlinie"), "short_evidence");

    expect(screen.getByText("Bitkom KI-Studie")).toBeInTheDocument();
    expect(screen.queryByText("Gesperrte Quelle")).not.toBeInTheDocument();
  });

  it("filters by source type", async () => {
    const user = userEvent.setup();
    render(<SourceExplorer sources={sources} />);

    await user.selectOptions(screen.getByLabelText("Quellentyp"), "official_statistics");

    expect(screen.getByText("Destatis KI-Nutzung")).toBeInTheDocument();
    expect(screen.queryByText("Bitkom KI-Studie")).not.toBeInTheDocument();
  });

  it("shows an empty state when no source matches the filters", async () => {
    const user = userEvent.setup();
    render(<SourceExplorer sources={sources} />);

    await user.type(screen.getByLabelText("Suche"), "does-not-exist-anywhere");

    expect(screen.getByText("Keine Quellen gefunden")).toBeInTheDocument();
  });
});
