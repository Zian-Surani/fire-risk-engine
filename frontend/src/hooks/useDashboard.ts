"use client";
/**
 * Generic polling hook for dashboard pages.
 *
 * Polls `fetcher` every `intervalMs` milliseconds and exposes:
 *   data     – latest parsed envelope or null
 *   loading  – true only on first load
 *   error    – last error string or null
 *   refresh  – imperative re-fetch
 */

import { useCallback, useEffect, useRef, useState } from "react";

interface Options<T> {
  /** Async function that returns fresh data */
  fetcher: () => Promise<T>;
  /** Poll interval in ms (default: 5000) */
  intervalMs?: number;
  /** Immediately fetch on mount (default: true) */
  immediate?: boolean;
}

interface State<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useDashboard<T>({
  fetcher,
  intervalMs = 5000,
  immediate = true,
}: Options<T>): State<T> & { refresh: () => void } {
  const [state, setState] = useState<State<T>>({
    data: null,
    loading: immediate,
    error: null,
  });

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fetcherRef = useRef(fetcher);

  useEffect(() => {
    fetcherRef.current = fetcher;
  }, [fetcher]);

  const refresh = useCallback(async () => {
    try {
      const data = await fetcherRef.current();
      setState({ data, loading: false, error: null });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setState((prev) => ({ ...prev, loading: false, error: message }));
    }
  }, []);

  useEffect(() => {
    if (immediate) {
      void refresh();
    }

    timerRef.current = setInterval(() => {
      void refresh();
    }, intervalMs);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [refresh, intervalMs, immediate]);

  return { ...state, refresh };
}
