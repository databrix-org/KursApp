"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@repo/api-client";
import { useLocale } from "next-intl";
import { dictionary } from "@repo/i18n";
export function useText() {
  return dictionary(useLocale());
}
export function useResource<T>(path: string | null) {
  const [data, setData] = useState<T>(),
    [error, setError] = useState(""),
    controller = useRef<AbortController | null>(null);
  const reload = useCallback(async () => {
    controller.current?.abort();
    if (!path) return;
    const current = new AbortController();
    controller.current = current;
    try {
      const value = await api<T>(path, { signal: current.signal });
      if (!current.signal.aborted) {
        setData(value);
        setError("");
      }
    } catch (e) {
      if (!current.signal.aborted)
        setError(e instanceof Error ? e.message : "Request failed");
    }
  }, [path]);
  useEffect(() => {
    setData(undefined);
    setError("");
    void reload();
    return () => controller.current?.abort();
  }, [reload]);
  return { data, error, reload, setData };
}
