"use client";

import { useState } from "react";
import { useDemo } from "@/lib/store";
import { fmtTime } from "@/lib/format";
import { EventDot } from "@/components/Chips";
import { Card, ButtonLink, Button } from "@/components/ui";
import type { WebhookEvent } from "@/lib/types";

export default function EventsPage() {
  const events = useDemo((s) => s.events);
  const mode = useDemo((s) => s.mode);
  const syncing = useDemo((s) => s.syncing);
  const refresh = useDemo((s) => s.refresh);
  const [selected, setSelected] = useState<string | null>(null);

  const active = events.find((e) => e.id === selected) ?? events[0] ?? null;
  const live = mode === "live";

  return (
    <div className="mx-auto max-w-6xl px-5 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="kicker text-smoke flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-volt live-dot" />
            {live ? "Live feed · from Somba" : "Live feed"}
          </p>
          <h1 className="display text-4xl md:text-5xl mt-2">Webhook events</h1>
          <p className="mt-2 text-smoke max-w-xl">
            Every billing action Somba takes is delivered to GymFlow as a signed
            webhook. This is that stream — exactly what a merchant&apos;s backend
            receives.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          {live && (
            <Button variant="outline" onClick={() => refresh()} disabled={syncing}>
              {syncing ? "Syncing…" : "Sync from Somba"}
            </Button>
          )}
          <ButtonLink href="/membership" variant="ghost">
            Membership
          </ButtonLink>
        </div>
      </div>

      {events.length === 0 ? (
        <Card className="mt-8 p-12 text-center">
          <p className="display text-2xl">No events yet</p>
          <p className="mt-2 text-sm text-smoke">
            Head to your membership and run a scenario from the demo cockpit —
            events will stream in here.
          </p>
        </Card>
      ) : (
        <div className="mt-8 grid lg:grid-cols-[1fr_0.9fr] gap-6 items-start">
          <Card className="overflow-hidden">
            <div className="px-5 py-3 border-b border-concrete-2 flex items-center justify-between">
              <span className="kicker text-smoke">Stream</span>
              <span className="mono text-xs text-smoke-2">{events.length} events</span>
            </div>
            <ul className="divide-y divide-concrete-2 max-h-[32rem] overflow-y-auto">
              {events.map((e) => (
                <li key={e.id}>
                  <button
                    onClick={() => setSelected(e.id)}
                    className={`w-full text-left px-5 py-3.5 flex items-center gap-3 transition-colors ${
                      active?.id === e.id ? "bg-concrete" : "hover:bg-concrete/60"
                    }`}
                  >
                    <EventDot type={e.type} />
                    <div className="flex-1 min-w-0">
                      <div className="mono text-xs font-semibold text-ink flex items-center gap-2">
                        {e.type}
                        <SourceTag source={e.source} />
                      </div>
                      <div className="text-xs text-smoke truncate">{e.summary}</div>
                    </div>
                    <span className="mono text-[11px] text-smoke-2 shrink-0">
                      {e.source === "live"
                        ? e.status ?? "delivered"
                        : e.created_at
                          ? fmtTime(e.created_at)
                          : ""}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </Card>

          <div className="lg:sticky lg:top-24">
            {active && <EventInspector event={active} />}
          </div>
        </div>
      )}
    </div>
  );
}

function SourceTag({ source }: { source?: string }) {
  if (source === "live")
    return (
      <span className="mono text-[9px] uppercase tracking-wide text-volt-deep border border-volt-deep/40 rounded px-1 py-px">
        live
      </span>
    );
  return (
    <span className="mono text-[9px] uppercase tracking-wide text-smoke-2 border border-concrete-2 rounded px-1 py-px">
      sim
    </span>
  );
}

function EventInspector({ event }: { event: WebhookEvent }) {
  const body = {
    id: event.id,
    type: event.type,
    ...(event.status ? { status: event.status } : {}),
    data: event.payload,
  };
  const isLive = event.source === "live";
  return (
    <Card className="overflow-hidden">
      <div className="px-5 py-3 border-b border-concrete-2 flex items-center gap-2">
        <EventDot type={event.type} />
        <span className="mono text-sm font-semibold">{event.type}</span>
        <SourceTag source={event.source} />
      </div>
      <div className="p-5 space-y-4">
        <div>
          <p className="kicker text-smoke-2 mb-1">Delivery</p>
          {isLive ? (
            <p className="text-sm text-smoke">
              Outbox status:{" "}
              <span
                className={`font-semibold ${event.status === "published" ? "text-volt-deep" : "text-due"}`}
              >
                {event.status ?? "pending"}
              </span>{" "}
              · signed per-merchant on delivery
            </p>
          ) : (
            <p className="text-sm">
              <span className="inline-flex items-center gap-1.5 text-volt-deep font-semibold">
                ✓ Delivered
              </span>{" "}
              <span className="text-smoke">· 1st attempt · {fmtTime(event.created_at)}</span>
            </p>
          )}
        </div>
        {!isLive && (
          <div>
            <p className="kicker text-smoke-2 mb-1">Signature (HMAC-SHA256)</p>
            <p className="mono text-xs text-smoke break-all">{event.signature}</p>
          </div>
        )}
        <div>
          <p className="kicker text-smoke-2 mb-1">Payload</p>
          <pre className="mono text-xs bg-ink text-paper/90 rounded-lg p-4 overflow-x-auto">
            {JSON.stringify(body, null, 2)}
          </pre>
        </div>
      </div>
    </Card>
  );
}
