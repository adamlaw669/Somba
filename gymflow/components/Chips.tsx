import type { InvoiceStatus } from "@/lib/types";

const INVOICE_CHIP: Record<InvoiceStatus, { label: string; cls: string }> = {
  paid: { label: "Paid", cls: "bg-volt text-ink border-ink/10" },
  open: { label: "Open", cls: "bg-due/15 text-due border-due/40" },
  draft: { label: "Draft", cls: "bg-concrete-2 text-smoke border-concrete-2" },
  void: { label: "Void", cls: "bg-danger/10 text-danger border-danger/30" },
  uncollectible: {
    label: "Uncollectible",
    cls: "bg-danger/10 text-danger border-danger/30",
  },
};

export function InvoiceChip({ status }: { status: InvoiceStatus }) {
  const c = INVOICE_CHIP[status];
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${c.cls}`}
    >
      {c.label}
    </span>
  );
}

// Event feed dot colour by family of event.
function eventTone(type: string): string {
  if (type.includes("succeeded") || type.includes("recovered") || type === "subscription.active" || type === "payment.resolved" || type === "transfer.reconciled")
    return "bg-volt";
  if (type.includes("failed") || type === "anomaly.detected") return "bg-danger";
  if (type === "payment.uncertain") return "bg-frozen";
  if (type.includes("past_due") || type.includes("retrying") || type === "transfer.requested")
    return "bg-due";
  return "bg-smoke";
}

export function EventDot({ type }: { type: string }) {
  return <span className={`h-2 w-2 rounded-full ${eventTone(type)}`} aria-hidden />;
}
