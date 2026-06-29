"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useDemo, useHydrated } from "@/lib/store";

const NAV = [
  { href: "/membership", label: "Membership" },
  { href: "/membership/billing", label: "Billing" },
  { href: "/membership/recovery", label: "Recovery" },
  { href: "/membership/card", label: "Card" },
  { href: "/events", label: "Events" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const hydrated = useHydrated();
  const hasSub = useDemo((s) => s.subscription !== null);
  const eventCount = useDemo((s) => s.events.length);

  return (
    <header className="sticky top-0 z-40 border-b border-concrete-2 bg-paper/85 backdrop-blur">
      <div className="mx-auto max-w-6xl px-5 h-16 flex items-center justify-between gap-4">
        <Link href="/" className="display text-ink text-2xl leading-none shrink-0">
          Gym<span className="text-volt-deep">Flow</span>
        </Link>

        {hydrated && hasSub && (
          <nav className="hidden md:flex items-center gap-1">
            {NAV.map((n) => {
              const active =
                n.href === "/membership"
                  ? pathname === "/membership"
                  : pathname.startsWith(n.href);
              return (
                <Link
                  key={n.href}
                  href={n.href}
                  className={`relative px-3 py-2 text-sm font-semibold rounded-full transition-colors ${
                    active
                      ? "bg-ink text-paper"
                      : "text-smoke hover:text-ink hover:bg-concrete"
                  }`}
                >
                  {n.label}
                  {n.href === "/events" && eventCount > 0 && (
                    <span className="ml-1.5 mono text-[10px] text-volt-deep">
                      {eventCount}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        )}

        <div className="flex items-center gap-2">
          <span className="hidden sm:flex items-center gap-1.5 kicker text-smoke-2">
            <span className="h-1.5 w-1.5 rounded-full bg-volt live-dot" />
            Powered by Somba
          </span>
        </div>
      </div>

      {hydrated && hasSub && (
        <nav className="md:hidden flex items-center gap-1 overflow-x-auto px-5 pb-2 border-t border-concrete-2 pt-2">
          {NAV.map((n) => {
            const active =
              n.href === "/membership"
                ? pathname === "/membership"
                : pathname.startsWith(n.href);
            return (
              <Link
                key={n.href}
                href={n.href}
                className={`px-3 py-1.5 text-xs font-semibold rounded-full whitespace-nowrap ${
                  active ? "bg-ink text-paper" : "text-smoke bg-concrete"
                }`}
              >
                {n.label}
              </Link>
            );
          })}
        </nav>
      )}
    </header>
  );
}
