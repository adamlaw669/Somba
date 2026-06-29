"use client";

import { useState } from "react";
import { useDemo } from "@/lib/store";
import { fmtTime } from "@/lib/format";
import { EventDot } from "@/components/Chips";
import { Card, ButtonLink } from "@/components/ui";
import type { WebhookEvent } from "@/lib/types";

export default function EventsPage() {
  const events = useDemo((s) => s.events);
  const [selected, setSelected] = useState<string | null>(null);

  const active = events.find((e) => e.id === selected) ?? events[0] ?? null;

  return (
    <div className="mx-auto max-w-6xl px-5 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="kicker text-smoke flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-volt live-dot" />
            Live feed
          </p>
          <h1 className="display text-4xl md:text-5xl mt-2">Webhook events</h1>
          <p className="mt-2 text-smoke max-w-xl">
            Every billing action Somba takes is delivered to GymFlow as a signed
            webhook. This is that stream — exactly what a merchant&apos;s backend
            receives.
          </p>
        </div>
        <ButtonLink href="/membership" variant="outline">
          Back to membership
        </ButtonLink>
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
          {/* the stream */}
          <Card className="overflow-hidden">
            <div className="px-5 py-3 border-b border-concrete-2 flex items-center justify-between">
              <span className="kicker text-smoke">Stream</span>
              <span className="mono text-xs text-smoke-2">
                {events.length} events
              </span>
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
                      <div className="mono text-xs font-semibold text-ink">
                        {e.type}
                      </div>
                      <div className="text-xs text-smoke truncate">
                        {e.summary}
                      </div>
                    </div>
                    <span className="mono text-[11px] text-smoke-2 shrink-0">
                      {fmtTime(e.created_at)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </Card>

          {/* payload inspector */}
          <div className="lg:sticky lg:top-24">
            {active && <EventInspector event={active} />}
          </div>
        </div>
      )}
    </div>
  );
}

function EventInspector({ event }: { event: WebhookEvent }) {
  const body = {
    id: event.id,
    type: event.type,
    created: event.created_at,
    data: event.payload,
  };
  return (
    <Card className="overflow-hidden">
      <div className="px-5 py-3 border-b border-concrete-2 flex items-center gap-2">
        <EventDot type={event.type} />
        <span className="mono text-sm font-semibold">{event.type}</span>
      </div>
      <div className="p-5 space-y-4">
        <div>
          <p className="kicker text-smoke-2 mb-1">Delivery</p>
          <p className="text-sm">
            <span className="inline-flex items-center gap-1.5 text-volt-deep font-semibold">
              ✓ Delivered
            </span>{" "}
            <span className="text-smoke">
              · 1st attempt · {fmtTime(event.created_at)}
            </span>
          </p>
        </div>
        <div>
          <p className="kicker text-smoke-2 mb-1">Signature (HMAC-SHA256)</p>
          <p className="mono text-xs text-smoke break-all">{event.signature}</p>
        </div>
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
