"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { useEffect, useState } from "react";
import { planById } from "./plans";
import { prorate } from "./money";
import type {
  ChargeAttempt,
  Customer,
  FailureClass,
  Invoice,
  Subscription,
  TransferRequest,
  WebhookEvent,
  WebhookEventType,
} from "./types";

// ---------- small helpers ----------
const now = () => new Date().toISOString();
const uid = (p: string) =>
  `${p}_${Math.random().toString(36).slice(2, 10)}${Math.random()
    .toString(36)
    .slice(2, 6)}`;
const addDays = (iso: string, d: number) => {
  const x = new Date(iso);
  x.setDate(x.getDate() + d);
  return x.toISOString();
};
const addMonth = (iso: string, m = 1) => {
  const x = new Date(iso);
  x.setMonth(x.getMonth() + m);
  return x.toISOString();
};
const period = (iso: string) => iso.slice(0, 7); // YYYY-MM
const fakeSig = () =>
  `t=${Math.floor(Date.now() / 1000)},v1=${Array.from({ length: 16 }, () =>
    Math.floor(Math.random() * 16).toString(16),
  ).join("")}`;

export interface DemoState {
  customer: Customer | null;
  subscription: Subscription | null;
  invoices: Invoice[];
  charges: ChargeAttempt[];
  events: WebhookEvent[];
  transfer: TransferRequest | null;
  selectedPlanId: string | null;

  selectPlan: (id: string) => void;
  signup: (input: {
    name: string;
    email: string;
    cardLast4: string;
    cardBrand: string;
    planId: string;
  }) => void;
  activateFromTrial: () => void;
  renew: () => void;
  triggerFailure: (failureClass: FailureClass) => void;
  triggerTimeout: () => void;
  retryPayment: () => void;
  simulateTransferPush: () => void;
  resolveUncertain: (succeeded: boolean) => void;
  pause: () => void;
  resume: () => void;
  cancel: () => void;
  changePlan: (newPlanId: string) => void;
  updateCard: (last4: string, brand: string) => void;
  reset: () => void;
}

const FAILURE_COPY: Record<
  FailureClass,
  { reason: string; nomba: string }
> = {
  empty_account: {
    reason: "Account had no funds at the time of the charge.",
    nomba: "insufficient_funds",
  },
  broken_card: {
    reason: "The card is expired or was hard-declined by the bank.",
    nomba: "card_declined",
  },
  transient: {
    reason: "A temporary soft decline — the bank said try again later.",
    nomba: "do_not_honour",
  },
  risk: {
    reason: "The bank flagged this payment as a risk and blocked it.",
    nomba: "security_violation",
  },
  unknown: {
    reason: "The result of the charge could not be determined.",
    nomba: "processor_unavailable",
  },
};

export const useDemo = create<DemoState>()(
  persist(
    (set, get) => {
      // internal: append a webhook event to the live feed
      const emit = (
        type: WebhookEventType,
        summary: string,
        payload: Record<string, unknown> = {},
      ) => {
        const evt: WebhookEvent = {
          id: uid("evt"),
          type,
          summary,
          created_at: now(),
          delivered: true,
          signature: fakeSig(),
          payload,
        };
        set((s) => ({ events: [evt, ...s.events].slice(0, 60) }));
      };

      const attemptNumber = (invoiceId: string) =>
        get().charges.filter((c) => c.invoice_id === invoiceId).length + 1;

      const newInvoice = (
        sub: Subscription,
        amount: number,
        type: Invoice["type"] = "regular",
      ): Invoice => {
        const inv: Invoice = {
          id: uid("in"),
          subscription_id: sub.id,
          amount,
          status: "open",
          type,
          period_start: sub.current_period_start,
          period_end: sub.current_period_end,
          created_at: now(),
          paid_at: null,
        };
        set((s) => ({ invoices: [inv, ...s.invoices] }));
        emit("invoice.created", `Invoice for ${formatKobo(amount)} created`, {
          invoice_id: inv.id,
          amount,
          type,
        });
        return inv;
      };

      const recordCharge = (
        sub: Subscription,
        inv: Invoice,
        status: ChargeAttempt["status"],
        opts: { failure_class?: FailureClass; failure_reason?: string } = {},
      ): ChargeAttempt => {
        const n = attemptNumber(inv.id);
        const ch: ChargeAttempt = {
          id: uid("ch"),
          invoice_id: inv.id,
          idempotency_key: `charge_${sub.id}_${period(
            inv.period_start,
          )}_${n}`,
          order_reference: uid("ord").toUpperCase(),
          amount: inv.amount,
          status,
          failure_reason: opts.failure_reason ?? null,
          failure_class: opts.failure_class ?? null,
          attempt_number: n,
          created_at: now(),
        };
        set((s) => ({ charges: [ch, ...s.charges] }));
        return ch;
      };

      const settle = (invId: string) =>
        set((s) => ({
          invoices: s.invoices.map((i) =>
            i.id === invId ? { ...i, status: "paid", paid_at: now() } : i,
          ),
        }));

      const setStatus = (status: Subscription["status"]) =>
        set((s) => ({
          subscription: s.subscription
            ? { ...s.subscription, status }
            : null,
        }));

      return {
        customer: null,
        subscription: null,
        invoices: [],
        charges: [],
        events: [],
        transfer: null,
        selectedPlanId: null,

        selectPlan: (id) => set({ selectedPlanId: id }),

        signup: ({ name, email, cardLast4, cardBrand, planId }) => {
          const plan = planById(planId);
          if (!plan) return;
          const start = now();
          const customer: Customer = {
            id: uid("cus"),
            name,
            email,
            card_last4: cardLast4,
            card_brand: cardBrand,
            va_account_no: null,
            va_bank: null,
            credit_balance: 0,
          };
          const trialing = plan.trial_days > 0;
          const trial_end = trialing ? addDays(start, plan.trial_days) : null;
          const sub: Subscription = {
            id: uid("sub"),
            plan_id: plan.id,
            status: trialing ? "trialing" : "active",
            current_period_start: start,
            current_period_end: addMonth(start),
            next_bill_date: trialing ? trial_end! : addMonth(start),
            trial_end,
            created_at: start,
          };
          set({
            customer,
            subscription: sub,
            invoices: [],
            charges: [],
            transfer: null,
            events: [],
          });
          emit(
            "subscription.created",
            `${name} subscribed to ${plan.name}${
              trialing ? ` — ${plan.trial_days}-day trial` : ""
            }`,
            { subscription_id: sub.id, plan: plan.name, status: sub.status },
          );
          if (!trialing) {
            const inv = newInvoice(sub, plan.amount);
            recordCharge(sub, inv, "succeeded");
            settle(inv.id);
            emit("charge.succeeded", `First charge of ${formatKobo(
              plan.amount,
            )} succeeded`, { invoice_id: inv.id });
            emit("subscription.active", "Membership is now active", {
              subscription_id: sub.id,
            });
          }
        },

        activateFromTrial: () => {
          const { subscription } = get();
          if (!subscription || subscription.status !== "trialing") return;
          const plan = planById(subscription.plan_id)!;
          const inv = newInvoice(subscription, plan.amount);
          recordCharge(subscription, inv, "succeeded");
          settle(inv.id);
          setStatus("active");
          emit("charge.succeeded", `First charge of ${formatKobo(
            plan.amount,
          )} succeeded`, { invoice_id: inv.id });
          emit("subscription.active", "Trial converted — membership active", {
            subscription_id: subscription.id,
          });
        },

        renew: () => {
          const { subscription } = get();
          if (!subscription) return;
          const plan = planById(subscription.plan_id)!;
          const start = subscription.current_period_end;
          const next: Subscription = {
            ...subscription,
            status: "active",
            current_period_start: start,
            current_period_end: addMonth(start),
            next_bill_date: addMonth(start),
          };
          set({ subscription: next });
          const inv = newInvoice(next, plan.amount);
          recordCharge(next, inv, "succeeded");
          settle(inv.id);
          emit("charge.succeeded", `Renewal of ${formatKobo(
            plan.amount,
          )} succeeded`, { invoice_id: inv.id });
          emit("subscription.active", "Membership renewed for another month", {
            subscription_id: next.id,
          });
        },

        triggerFailure: (failureClass) => {
          const { subscription, customer } = get();
          if (!subscription || !customer) return;
          const plan = planById(subscription.plan_id)!;
          const copy = FAILURE_COPY[failureClass];
          const inv = newInvoice(subscription, plan.amount);
          recordCharge(subscription, inv, "failed", {
            failure_class: failureClass,
            failure_reason: copy.nomba,
          });
          emit("charge.failed", `Charge failed — ${copy.nomba}`, {
            invoice_id: inv.id,
            failure_class: failureClass,
          });

          if (failureClass === "risk") {
            setStatus("past_due");
            emit("anomaly.detected", "Risk block — merchant notified, retries stopped", {
              subscription_id: subscription.id,
            });
            emit("subscription.past_due", "Membership is past due", {
              subscription_id: subscription.id,
            });
            return;
          }

          if (failureClass === "broken_card") {
            // hard decline -> stop pulling, provision VA, request transfer
            const va = "8" + Math.floor(100000000 + Math.random() * 899999999);
            set((s) => ({
              customer: s.customer
                ? { ...s.customer, va_account_no: va, va_bank: "Nomba MFB" }
                : null,
              transfer: {
                account_no: va,
                bank: "Nomba MFB",
                amount: inv.amount,
                reference: inv.id.toUpperCase(),
                invoice_id: inv.id,
              },
            }));
            setStatus("past_due");
            emit("transfer.requested", `Transfer of ${formatKobo(
              inv.amount,
            )} requested to dedicated account`, {
              account_no: va,
              amount: inv.amount,
            });
            emit("subscription.past_due", "Membership is past due — transfer requested", {
              subscription_id: subscription.id,
            });
            return;
          }

          if (failureClass === "transient") {
            // one immediate retry, still fails -> past_due
            recordCharge(subscription, inv, "failed", {
              failure_class: failureClass,
              failure_reason: copy.nomba,
            });
            emit("charge.retrying", "Soft decline — one immediate retry", {
              invoice_id: inv.id,
            });
          }

          // empty_account / transient / unknown -> timing recovery, keep access
          setStatus("past_due");
          emit("subscription.past_due", "Membership past due — retry scheduled for a funding window", {
            subscription_id: subscription.id,
          });
        },

        triggerTimeout: () => {
          const { subscription } = get();
          if (!subscription) return;
          const plan = planById(subscription.plan_id)!;
          const inv = newInvoice(subscription, plan.amount);
          recordCharge(subscription, inv, "uncertain", {
            failure_reason: "timeout_no_response",
          });
          setStatus("payment_uncertain");
          emit("payment.uncertain", "Charge timed out — subscription frozen pending verify", {
            invoice_id: inv.id,
            subscription_id: subscription.id,
          });
        },

        retryPayment: () => {
          const { subscription, invoices } = get();
          if (!subscription || subscription.status !== "past_due") return;
          const open = invoices.find((i) => i.status === "open");
          if (!open) return;
          recordCharge(subscription, open, "succeeded");
          settle(open.id);
          setStatus("active");
          set({ transfer: null });
          emit("charge.recovered", "Retry succeeded — payment recovered", {
            invoice_id: open.id,
          });
          emit("subscription.active", "Membership healed back to active", {
            subscription_id: subscription.id,
          });
        },

        simulateTransferPush: () => {
          const { subscription, transfer } = get();
          if (!subscription || !transfer) return;
          // orphan settlement arrives, reconciler maps it to the open invoice
          settle(transfer.invoice_id);
          setStatus("active");
          set({ transfer: null });
          emit("transfer.reconciled", `Transfer of ${formatKobo(
            transfer.amount,
          )} matched to open invoice`, {
            invoice_id: transfer.invoice_id,
            amount: transfer.amount,
          });
          emit("charge.recovered", "Payment recovered via transfer fallback", {
            invoice_id: transfer.invoice_id,
          });
          emit("subscription.active", "Membership healed back to active", {
            subscription_id: subscription.id,
          });
        },

        resolveUncertain: (succeeded) => {
          const { subscription, invoices } = get();
          if (!subscription || subscription.status !== "payment_uncertain")
            return;
          const open = invoices.find((i) => i.status === "open");
          if (succeeded) {
            if (open) settle(open.id);
            setStatus("active");
            emit("payment.resolved", "Verify pass confirmed success", {
              subscription_id: subscription.id,
            });
            emit("subscription.active", "Membership healed back to active", {
              subscription_id: subscription.id,
            });
          } else {
            setStatus("past_due");
            emit("payment.resolved", "Verify pass confirmed failure", {
              subscription_id: subscription.id,
            });
            emit("subscription.past_due", "Now in recovery — verified failure", {
              subscription_id: subscription.id,
            });
          }
        },

        pause: () => {
          const { subscription } = get();
          if (!subscription) return;
          setStatus("paused");
          emit("subscription.paused", "Membership paused — no billing runs", {
            subscription_id: subscription.id,
          });
        },

        resume: () => {
          const { subscription } = get();
          if (!subscription) return;
          setStatus("active");
          emit("subscription.resumed", "Membership resumed", {
            subscription_id: subscription.id,
          });
        },

        cancel: () => {
          const { subscription } = get();
          if (!subscription) return;
          set((s) => ({
            subscription: s.subscription
              ? { ...s.subscription, status: "cancelled", next_bill_date: "" }
              : null,
            transfer: null,
          }));
          emit("subscription.cancelled", "Membership cancelled — no further billing", {
            subscription_id: subscription.id,
          });
        },

        changePlan: (newPlanId) => {
          const { subscription, customer } = get();
          if (!subscription || !customer) return;
          const oldPlan = planById(subscription.plan_id)!;
          const newPlan = planById(newPlanId)!;
          if (oldPlan.id === newPlan.id) return;

          const daysInPeriod = 30;
          const msLeft =
            new Date(subscription.current_period_end).getTime() - Date.now();
          const daysRemaining = Math.max(
            0,
            Math.min(daysInPeriod, Math.round(msLeft / 86_400_000)),
          );
          const { credit, charge, net } = prorate(
            oldPlan.amount,
            newPlan.amount,
            daysInPeriod,
            daysRemaining,
          );

          set((s) => ({
            subscription: s.subscription
              ? { ...s.subscription, plan_id: newPlan.id }
              : null,
          }));
          emit(
            "subscription.updated",
            `Plan changed: ${oldPlan.name} → ${newPlan.name}`,
            { credit, charge, net, days_remaining: daysRemaining },
          );

          if (net > 0) {
            const sub = get().subscription!;
            const inv = newInvoice(sub, net, "proration");
            recordCharge(sub, inv, "succeeded");
            settle(inv.id);
            emit("charge.succeeded", `Proration charge of ${formatKobo(
              net,
            )} succeeded`, { invoice_id: inv.id });
          } else if (net < 0) {
            set((s) => ({
              customer: s.customer
                ? {
                    ...s.customer,
                    credit_balance: s.customer.credit_balance - net,
                  }
                : null,
            }));
            emit(
              "subscription.updated",
              `Downgrade credit of ${formatKobo(-net)} banked for next renewal`,
              { credit: -net },
            );
          }
        },

        updateCard: (last4, brand) => {
          set((s) => ({
            customer: s.customer
              ? { ...s.customer, card_last4: last4, card_brand: brand }
              : null,
          }));
          const { subscription } = get();
          if (subscription) {
            emit("subscription.updated", `Card updated — now •••• ${last4}`, {
              subscription_id: subscription.id,
            });
          }
        },

        reset: () =>
          set({
            customer: null,
            subscription: null,
            invoices: [],
            charges: [],
            events: [],
            transfer: null,
            selectedPlanId: null,
          }),
      };
    },
    {
      name: "gymflow-demo",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);

// local copy to avoid importing money fmt into closures repeatedly
function formatKobo(kobo: number): string {
  return `₦${(kobo / 100).toLocaleString("en-NG")}`;
}

/** Avoids hydration mismatch: returns true only after the persisted store mounts. */
export function useHydrated(): boolean {
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => setHydrated(true), []);
  return hydrated;
}
