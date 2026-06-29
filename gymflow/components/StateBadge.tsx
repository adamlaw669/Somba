import { STATE_META } from "@/lib/states";
import type { SubscriptionStatus } from "@/lib/types";

export function StateBadge({
  status,
  size = "md",
}: {
  status: SubscriptionStatus;
  size?: "sm" | "md" | "lg";
}) {
  const m = STATE_META[status];
  const pad =
    size === "lg"
      ? "px-4 py-2 text-sm"
      : size === "sm"
        ? "px-2.5 py-1 text-[11px]"
        : "px-3 py-1.5 text-xs";
  return (
    <span
      className={`inline-flex items-center gap-2 border rounded-full font-semibold uppercase tracking-wide ${m.badge} ${pad}`}
    >
      <span className={`h-2 w-2 rounded-full ${m.dot}`} aria-hidden />
      {m.label}
    </span>
  );
}
