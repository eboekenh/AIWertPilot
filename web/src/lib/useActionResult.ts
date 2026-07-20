"use client";

import { useCallback, useState, useTransition } from "react";

import type { ActionResult } from "@/lib/api/types";

/** Shared plumbing for calling a Server Action from a client component and
 * rendering its ActionResult<T> inline (pending state + success/error
 * result), without ever throwing an uncaught exception into the UI. */
export function useActionResult<T>() {
  const [isPending, startTransition] = useTransition();
  const [result, setResult] = useState<ActionResult<T> | null>(null);

  const execute = useCallback((run: () => Promise<ActionResult<T>>) => {
    setResult(null);
    startTransition(() => {
      void run().then(setResult);
    });
  }, []);

  const reset = useCallback(() => setResult(null), []);

  return { execute, isPending, result, reset };
}
