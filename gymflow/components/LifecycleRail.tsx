import { LIFECYCLE, STATE_META } from "@/lib/states";
import type { SubscriptionStatus } from "@/lib/types";

// The 7-state lifecycle as an ordered rail. The current state is lit in volt.
export function LifecycleRail({ current }: { current: SubscriptionStatus }) {
  return (
    <div className="overflow-x-auto">
      <ol className="flex items-stretch gap-1 min-w-max">
        {LIFECYCLE.map((s, i) => {
          const active = s === current;
          const m = STATE_META[s];
          return (
            <li key={s} className="flex items-center gap-1">
              <div
                className={`flex flex-col gap-1 rounded-lg border px-3 py-2 transition-colors ${
                  active
                    ? "bg-ink text-paper border-ink"
                    : "bg-paper text-smoke border-concrete-2"
                }`}
              >
                <span
                  className={`mono text-[10px] ${active ? "text-volt" : "text-smoke-2"}`}
                >
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="text-xs font-semibold whitespace-nowrap flex items-center gap-1.5">
                  <span className={`h-1.5 w-1.5 rounded-full ${m.dot}`} />
                  {m.label}
                </span>
              </div>
              {i < LIFECYCLE.length - 1 && (
                <span className="text-concrete-2 select-none" aria-hidden>
                  ›
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
