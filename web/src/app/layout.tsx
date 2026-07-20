import type { Metadata } from "next";

import { AppShell } from "@/components/layout/AppShell";

import "./globals.css";

export const metadata: Metadata = {
  title: "AIWertPilot",
  description: "AIWertPilot — internes Evidenz- und Quellenprüfungswerkzeug",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="de">
      <body className="font-sans antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
