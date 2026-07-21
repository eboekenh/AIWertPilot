import Link from "next/link";

import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/ui/EmptyState";

export default function NotFound() {
  return (
    <>
      <PageHeader title="Nicht gefunden" />
      <EmptyState
        title="Seite oder Quelle nicht gefunden"
        description="Der angeforderte Inhalt existiert nicht oder wurde entfernt."
        action={
          <Link href="/" className="text-sm font-medium text-slate-900 underline dark:text-slate-100">
            Zur Übersicht
          </Link>
        }
      />
    </>
  );
}
