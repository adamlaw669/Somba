"use client";

import { useDemo } from "@/lib/store";
import { planById } from "@/lib/plans";
import { naira } from "@/lib/money";
import { fmtDate } from "@/lib/format";
import { InvoiceChip } from "@/components/Chips";
import { Card, ButtonLink } from "@/components/ui";

const CHARGE_TONE: Record<string, string> = {
  succeeded: "text-volt-deep",
  failed: "text-danger",
  uncertain: "text-frozen",
  pending: "text-smoke",
};

export default function BillingPage() {
  const invoices = useDemo((s) => s.invoices);
  const charges = useDemo((s) => s.charges);
  const sub = useDemo((s) => s.subscription)!;
  const plan = planById(sub.plan_id);

  const totalPaid = invoices
    .filter((i) => i.status === "paid")
    .reduce((sum, i) => sum + i.amount, 0);

  return (
    <div className="mx-auto max-w-6xl px-5 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="kicker text-smoke">Billing</p>
          <h1 className="display text-4xl md:text-5xl mt-2">Payment history</h1>
        </div>
        <ButtonLink href="/membership/card" variant="outline">
          Update payment method
        </ButtonLink>
      </div>

      <div className="mt-8 grid sm:grid-cols-3 gap-4">
        <Stat label="Paid to date" value={naira(totalPaid)} />
        <Stat
          label="Invoices"
          value={String(invoices.length)}
        />
        <Stat
          label={sub.status === "trialing" ? "First bill" : "Next bill"}
          value={
            plan && sub.status !== "cancelled"
              ? naira(plan.amount)
              : "—"
          }
          hint={
            sub.status === "cancelled"
              ? "Cancelled"
              : fmtDate(
                  sub.status === "trialing" ? sub.trial_end : sub.next_bill_date,
                )
          }
        />
      </div>

      {/* invoices */}
      <h2 className="kicker text-smoke mt-12 mb-3">Invoices</h2>
      <Card className="overflow-hidden">
        {invoices.length === 0 ? (
          <div className="p-10 text-center">
            <p className="display text-2xl">No invoices yet</p>
            <p className="mt-2 text-sm text-smoke">
              Your first invoice appears as soon as billing starts.
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-concrete-2">
            {invoices.map((inv) => (
              <li
                key={inv.id}
                className="flex items-center gap-4 px-5 py-4 hover:bg-concrete/60 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">
                      {inv.type === "proration"
                        ? "Plan change (prorated)"
                        : `${plan?.name ?? "Membership"} — monthly`}
                    </span>
                    {inv.type === "proration" && (
                      <span className="mono text-[10px] text-smoke-2 uppercase">
                        proration
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-smoke-2 mt-0.5">
                    {fmtDate(inv.period_start)} – {fmtDate(inv.period_end)}
                    {inv.paid_at && ` · paid ${fmtDate(inv.paid_at)}`}
                  </div>
                </div>
                <span className="display text-xl tabular-nums">
                  {naira(inv.amount)}
                </span>
                <div className="w-28 flex justify-end">
                  <InvoiceChip status={inv.status} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* charge attempts / ledger — the correctness proof */}
      <h2 className="kicker text-smoke mt-12 mb-1">Charge attempts</h2>
      <p className="text-sm text-smoke mb-3 max-w-2xl">
        Every attempt carries a unique idempotency key and order reference, so a
        retry can never charge you twice. This is the same ledger Somba uses to
        prove where every naira went.
      </p>
      <Card className="overflow-x-auto">
        {charges.length === 0 ? (
          <div className="p-10 text-center text-sm text-smoke">
            No charge attempts yet.
          </div>
        ) : (
          <table className="w-full text-sm min-w-[640px]">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-smoke-2 border-b border-concrete-2">
                <th className="px-5 py-3 font-semibold">Idempotency key</th>
                <th className="px-3 py-3 font-semibold">Order ref</th>
                <th className="px-3 py-3 font-semibold">Amount</th>
                <th className="px-3 py-3 font-semibold">Try</th>
                <th className="px-5 py-3 font-semibold text-right">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-concrete-2">
              {charges.map((c) => (
                <tr key={c.id} className="hover:bg-concrete/60">
                  <td className="px-5 py-3 mono text-xs text-ink/80">
                    {c.idempotency_key}
                  </td>
                  <td className="px-3 py-3 mono text-xs text-smoke">
                    {c.order_reference.slice(0, 12)}
                  </td>
                  <td className="px-3 py-3 tabular-nums">{naira(c.amount)}</td>
                  <td className="px-3 py-3 mono text-xs">#{c.attempt_number}</td>
                  <td
                    className={`px-5 py-3 text-right font-semibold uppercase text-xs ${CHARGE_TONE[c.status]}`}
                  >
                    {c.status}
                    {c.failure_reason && (
                      <span className="block text-[10px] text-smoke-2 normal-case font-normal">
                        {c.failure_reason}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}

function Stat({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <Card className="p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-smoke-2">
        {label}
      </p>
      <p className="display text-3xl mt-1.5">{value}</p>
      {hint && <p className="text-xs text-smoke-2 mt-1">{hint}</p>}
    </Card>
  );
}
