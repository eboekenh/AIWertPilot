import Link from "next/link";

import { AccessPolicyBadge } from "@/components/badges/AccessPolicyBadge";
import { RightsBadge } from "@/components/badges/RightsBadge";
import { StatusBadge } from "@/components/badges/StatusBadge";
import type { SourceRead } from "@/lib/api/types";
import { formatDate } from "@/lib/format";

export function SourceTable({ sources }: { sources: SourceRead[] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
      <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
        <thead className="bg-slate-50 dark:bg-slate-900">
          <tr>
            <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-300">
              Quelle
            </th>
            <th
              scope="col"
              className="hidden px-4 py-3 text-left font-medium text-slate-600 sm:table-cell dark:text-slate-300"
            >
              Typ
            </th>
            <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-300">
              Status
            </th>
            <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-300">
              Rechte
            </th>
            <th
              scope="col"
              className="hidden px-4 py-3 text-left font-medium text-slate-600 md:table-cell dark:text-slate-300"
            >
              Zugriff
            </th>
            <th
              scope="col"
              className="hidden px-4 py-3 text-left font-medium text-slate-600 lg:table-cell dark:text-slate-300"
            >
              Zuletzt geprüft
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
          {sources.map((source) => (
            <tr key={source.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/60">
              <td className="px-4 py-3">
                <Link
                  href={`/sources/${source.id}`}
                  className="font-medium text-slate-900 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-500 dark:text-slate-100"
                >
                  {source.title}
                </Link>
                <div className="text-xs text-slate-500 dark:text-slate-400">
                  {source.source_key} · {source.publisher}
                </div>
              </td>
              <td className="hidden px-4 py-3 text-slate-600 sm:table-cell dark:text-slate-300">
                {source.source_type}
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={source.status} />
              </td>
              <td className="px-4 py-3">
                <RightsBadge rightsStatus={source.rights_status} />
              </td>
              <td className="hidden px-4 py-3 md:table-cell">
                <AccessPolicyBadge accessPolicy={source.access_policy} />
              </td>
              <td className="hidden px-4 py-3 text-slate-600 lg:table-cell dark:text-slate-300">
                {formatDate(source.last_verified_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
