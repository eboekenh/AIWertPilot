"use client";

import { ACCESS_POLICIES, RIGHTS_STATUSES, SOURCE_STATUSES } from "@/lib/api/types";
import { ACCESS_POLICY_META, RIGHTS_STATUS_META, SOURCE_STATUS_META, metaOrFallback } from "@/lib/enums";

export interface SourceFiltersValue {
  search: string;
  status: string;
  rightsStatus: string;
  accessPolicy: string;
  sourceType: string;
}

export interface SourceFiltersProps {
  value: SourceFiltersValue;
  onChange: (value: SourceFiltersValue) => void;
  sourceTypeOptions: string[];
}

const selectClass =
  "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100";

export function SourceFilters({ value, onChange, sourceTypeOptions }: SourceFiltersProps) {
  function set<K extends keyof SourceFiltersValue>(key: K, next: SourceFiltersValue[K]) {
    onChange({ ...value, [key]: next });
  }

  return (
    <fieldset className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
      <legend className="sr-only">Quellen filtern</legend>
      <div>
        <label htmlFor="source-search" className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
          Suche
        </label>
        <input
          id="source-search"
          type="search"
          placeholder="Titel, Kürzel oder Verlag…"
          value={value.search}
          onChange={(event) => set("search", event.target.value)}
          className={selectClass}
        />
      </div>
      <div>
        <label htmlFor="source-status" className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
          Status
        </label>
        <select
          id="source-status"
          value={value.status}
          onChange={(event) => set("status", event.target.value)}
          className={selectClass}
        >
          <option value="">Alle</option>
          {SOURCE_STATUSES.map((status) => (
            <option key={status} value={status}>
              {metaOrFallback(SOURCE_STATUS_META, status).label}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="source-rights" className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
          Rechtestatus
        </label>
        <select
          id="source-rights"
          value={value.rightsStatus}
          onChange={(event) => set("rightsStatus", event.target.value)}
          className={selectClass}
        >
          <option value="">Alle</option>
          {RIGHTS_STATUSES.map((status) => (
            <option key={status} value={status}>
              {metaOrFallback(RIGHTS_STATUS_META, status).label}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="source-access" className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
          Zugriffsrichtlinie
        </label>
        <select
          id="source-access"
          value={value.accessPolicy}
          onChange={(event) => set("accessPolicy", event.target.value)}
          className={selectClass}
        >
          <option value="">Alle</option>
          {ACCESS_POLICIES.map((policy) => (
            <option key={policy} value={policy}>
              {metaOrFallback(ACCESS_POLICY_META, policy).label}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="source-type" className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
          Quellentyp
        </label>
        <select
          id="source-type"
          value={value.sourceType}
          onChange={(event) => set("sourceType", event.target.value)}
          className={selectClass}
        >
          <option value="">Alle</option>
          {sourceTypeOptions.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </div>
    </fieldset>
  );
}
