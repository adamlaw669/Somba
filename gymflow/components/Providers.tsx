"use client";

import { useEffect } from "react";
import { useDemo } from "@/lib/store";

// Detects live vs local mode and, if a membership id is persisted, syncs it
// with the live Somba API on load.
export function Providers({ children }: { children: React.ReactNode }) {
  const bootstrap = useDemo((s) => s.bootstrap);
  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);
  return <>{children}</>;
}
