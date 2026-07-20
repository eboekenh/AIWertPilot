"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Übersicht" },
  { href: "/sources", label: "Quellen" },
  { href: "/review", label: "Prüfung" },
] as const;

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function NavBar() {
  const pathname = usePathname();

  return (
    <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-slate-100">
          <span
            aria-hidden="true"
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-sm font-bold text-white dark:bg-slate-100 dark:text-slate-900"
          >
            AW
          </span>
          AIWertPilot
        </Link>
        <nav aria-label="Hauptnavigation">
          <ul className="flex flex-wrap gap-1">
            {NAV_ITEMS.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={`rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-500 ${
                      active
                        ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </header>
  );
}
