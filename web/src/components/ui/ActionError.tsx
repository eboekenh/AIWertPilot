import type { ApiErrorDetail } from "@/lib/api/types";

interface FieldError {
  loc?: unknown[];
  msg?: string;
}

function fieldErrors(details: Record<string, unknown>): FieldError[] {
  const errors = details.errors;
  return Array.isArray(errors) ? (errors as FieldError[]) : [];
}

/** Renders a backend ApiErrorDetail safely: the top-level message always
 * comes from the backend's own user-facing text, and per-field validation
 * errors (RequestValidationError's details.errors, from FastAPI/Pydantic)
 * are listed individually when present. Never renders a raw stack trace or
 * exception string. */
export function ActionError({ error }: { error: ApiErrorDetail }) {
  const errors = fieldErrors(error.details ?? {});
  return (
    <div
      role="alert"
      className="rounded-md border border-rose-300 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-300"
    >
      <p className="font-medium">{error.message}</p>
      {errors.length > 0 ? (
        <ul className="mt-1 list-disc space-y-0.5 pl-5">
          {errors.map((fieldError, index) => (
            <li key={index}>
              {Array.isArray(fieldError.loc) ? fieldError.loc.join(".") : "Feld"}: {fieldError.msg}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
