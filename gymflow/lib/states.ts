import type { SubscriptionStatus } from "./types";

export interface StateMeta {
  label: string;
  plain: string; // plain-English meaning for the member
  // tailwind classes for the badge surface + text + dot
  badge: string;
  dot: string;
  tone: "good" | "warn" | "frozen" | "rest";
}

export const STATE_META: Record<SubscriptionStatus, StateMeta> = {
  trialing: {
    label: "Trialing",
    plain: "You're in your free trial. No charge yet.",
    badge: "bg-ink text-volt border-ink",
    dot: "bg-volt",
    tone: "good",
  },
  active: {
    label: "Active",
    plain: "Paid up and running. Everything's open to you.",
    badge: "bg-volt text-ink border-ink",
    dot: "bg-ink",
    tone: "good",
  },
  past_due: {
    label: "Past due",
    plain: "A payment didn't go through. You still have access while we recover it.",
    badge: "bg-due/15 text-due border-due/40",
    dot: "bg-due",
    tone: "warn",
  },
  payment_uncertain: {
    label: "Verifying",
    plain: "We're confirming a payment with the bank. Frozen until we know for sure.",
    badge: "bg-frozen/15 text-frozen border-frozen/40",
    dot: "bg-frozen",
    tone: "frozen",
  },
  paused: {
    label: "Paused",
    plain: "Billing is on hold. Resume whenever you're ready.",
    badge: "bg-concrete-2 text-rest border-rest/30",
    dot: "bg-rest",
    tone: "rest",
  },
  cancelled: {
    label: "Cancelled",
    plain: "This membership has ended. No further billing.",
    badge: "bg-concrete-2 text-rest border-rest/30",
    dot: "bg-rest",
    tone: "rest",
  },
  expired: {
    label: "Expired",
    plain: "This membership reached its natural end.",
    badge: "bg-concrete-2 text-rest border-rest/30",
    dot: "bg-rest",
    tone: "rest",
  },
};

// The full lifecycle as an ordered rail (a real sequence — numbering earns its place).
export const LIFECYCLE: SubscriptionStatus[] = [
  "trialing",
  "active",
  "past_due",
  "payment_uncertain",
  "paused",
  "cancelled",
];
