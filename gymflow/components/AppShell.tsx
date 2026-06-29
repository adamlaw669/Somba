"use client";

import Link from "next/link";
import { useDemo, useHydrated } from "@/lib/store";
import { SiteHeader } from "./SiteHeader";
import { ButtonLink } from "./ui";
import type { ReactNode } from "react";

// Wraps member-area pages. If no membership exists yet, nudges to the landing page.
export function AppShell({ children }: { children: ReactNode }) {
  const hydrated = useHydrated();
  const hasSub = useDemo((s) => s.subscription !== null);

  return (
    <div className="min-h-screen flex flex-col">
      <SiteHeader />
      <main className="flex-1">
        {!hydrated ? (
          <div className="mx-auto max-w-6xl px-5 py-20">
            <div className="h-8 w-40 bg-concrete-2 rounded animate-pulse" />
          </div>
        ) : hasSub ? (
          children
        ) : (
          <div className="mx-auto max-w-6xl px-5 py-24 text-center">
            <p className="kicker text-smoke">No membership yet</p>
            <h1 className="display text-4xl md:text-5xl mt-3">
              Nothing to show here — yet.
            </h1>
            <p className="mt-4 text-smoke max-w-md mx-auto">
              Join GymFlow to see the full membership lifecycle: trial, billing,
              recovery, and a pass that heals itself.
            </p>
            <div className="mt-8 flex justify-center">
              <ButtonLink href="/" variant="primary">
                Choose a plan
              </ButtonLink>
            </div>
          </div>
        )}
      </main>
      <SiteFooter />
    </div>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-concrete-2 mt-12">
      <div className="mx-auto max-w-6xl px-5 py-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-smoke">
        <div className="display text-ink text-lg">
          Gym<span className="text-volt-deep">Flow</span>
        </div>
        <p className="text-center sm:text-right">
          A demo of{" "}
          <Link href="/" className="text-ink font-semibold underline-offset-2 hover:underline">
            Somba
          </Link>{" "}
          — managed recurring billing & recovery. No real money moves.
        </p>
      </div>
    </footer>
  );
}
