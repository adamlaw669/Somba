"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { useEffect, useState } from "react";
import { planById } from "./plans";
import { prorate } from "./money";
import {
  api,
  type ApiCustomer,
  type ApiEvent,
  type ApiInvoice,
  type ApiPlan,
  type ApiProration,
  type ApiSubscription,
  type Tier,
} from "./api";
import type {
  ChargeAttempt,
  Customer,
  FailureClass,
  Invoice,
  Subscription,
  SubscriptionStatus,
  TransferRequest,
  WebhookEvent,
  WebhookEventType,
} from "./types";

// ---------- helpers ----------
const now = () => new Date().toISOString();
const uid = (p: string) =>
  `${p}_${Math.random().toString(36).slice(2, 10)}${Math.random().toString(36).slice(2, 6)}`;
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
const period = (iso: string) => iso.slice(0, 7);
const fakeSig = () =>
  `t=${Math.floor(Date.now() / 1000)},v1=${Array.from({ length: 16 }, () =>
    Math.floor(Math.random() * 16).toString(16),
  ).join("")}`;
const formatKobo = (kobo: number) => `₦${(kobo / 100).toLocaleString("en-NG")}`;

const tierOf = (localPlanId: string): Tier =>
  localPlanId.replace("plan_", "") as Tier;
const localPlanFor = (tier: Tier) => `plan_${tier}`;

// ---------- mapping API -> our view types ----------
function mapSub(
  s: ApiSubscription,
  realIdToTier: Record<number, Tier>,
): Subscription {
  const tier = realIdToTier[s.plan_id] ?? "standard";
  const start = s.current_period_start ?? now();
  return {
    id: String(s.id),
    plan_id: localPlanFor(tier),
    status: s.status as SubscriptionStatus,
    current_period_start: start,
    current_period_end: s.current_period_end ?? addMonth(start),
    next_bill_date: s.next_bill_date ?? "",
    trial_end: s.trial_end,
    created_at: start,
  };
}

function mapCustomer(
  c: ApiCustomer,
  card: { last4: string; brand: string } | null,
): Customer {
  return {
    id: String(c.id),
    name: c.name ?? "Member",
    email: c.email ?? "",
    card_last4: card?.last4 ?? "••••",
    card_brand: card?.brand ?? "Card",
    va_account_no: c.va_account_no,
    va_bank: c.va_account_no ? "Nomba MFB" : null,
    credit_balance: c.credit_balance ?? 0,
  };
}

function mapInvoice(i: ApiInvoice): Invoice {
  return {
    id: String(i.id),
    subscription_id: String(i.subscription_id),
    amount: i.amount,
    status: i.status as Invoice["status"],
    type: (i.type as Invoice["type"]) ?? "regular",
    period_start: i.period_start ?? now(),
    period_end: i.period_end ?? now(),
    created_at: i.period_start ?? now(),
    paid_at: i.paid_at,
  };
}

function summarizeLive(e: ApiEvent): string {
  const p = e.payload ?? {};
  const status = typeof p.status === "string" ? ` → ${p.status}` : "";
  switch (e.event_type) {
    case "subscription.created":
      return `Subscription created${status}`;
    case "invoice.created":
      return `Invoice created${p.amount ? ` for ${formatKobo(Number(p.amount))}` : ""}`;
    case "charge.succeeded":
      return "Charge succeeded";
    case "charge.failed":
      return "Charge failed";
    case "subscription.updated":
      return "Subscription updated";
    default:
      return e.event_type.replace(/\./g, " ");
  }
}

function mapLiveEvent(e: ApiEvent): WebhookEvent {
  return {
    id: `live_${e.id}`,
    seq: e.id,
    type: e.event_type,
    summary: summarizeLive(e),
    created_at: "",
    delivered: e.status === "published",
    signature: "",
    payload: e.payload ?? {},
    source: "live",
    status: e.status,
  };
}

// ---------- store ----------
type Mode = "loading" | "live" | "local";

const FAILURE_COPY: Record<FailureClass, { reason: string; nomba: string }> = {
  empty_account: { reason: "Account had no funds at the time of the charge.", nomba: "insufficient_funds" },
  broken_card: { reason: "The card is expired or was hard-declined by the bank.", nomba: "card_declined" },
  transient: { reason: "A temporary soft decline — the bank said try again later.", nomba: "do_not_honour" },
  risk: { reason: "The bank flagged this payment as a risk and blocked it.", nomba: "security_violation" },
  unknown: { reason: "The result of the charge could not be determined.", nomba: "processor_unavailable" },
};

export interface DemoState {
  mode: Mode;
  syncing: boolean;
  error: string | null;
  apiPlans: ApiPlan[];
  realIdToTier: Record<number, Tier>;
  subscriptionId: number | null;
  customerId: number | null;
  localCard: { last4: string; brand: string } | null;
  lastProration: ApiProration | null;

  customer: Customer | null;
  subscription: Subscription | null;
  invoices: Invoice[];
  charges: ChargeAttempt[];
  simEvents: WebhookEvent[];
  liveEvents: WebhookEvent[];
  events: WebhookEvent[];
  transfer: TransferRequest | null;
  selectedPlanId: string | null;

  bootstrap: () => Promise<void>;
  refresh: () => Promise<void>;
  selectPlan: (id: string) => void;
  signup: (input: {
    name: string;
    email: string;
    cardLast4: string;
    cardBrand: string;
    planId: string;
  }) => Promise<void>;
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
  changePlan: (newPlanId: string) => Promise<void>;
  updateCard: (last4: string, brand: string) => void;
  reset: () => void;
}

export const useDemo = create<DemoState>()(
  persist(
    (set, get) => {
      const rebuildFeed = () =>
        set((s) => ({ events: [...s.simEvents, ...s.liveEvents] }));

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
          source: "sim",
        };
        set((s) => ({ simEvents: [evt, ...s.simEvents].slice(0, 60) }));
        rebuildFeed();
      };

      const setStatus = (status: SubscriptionStatus) =>
        set((s) => ({
          subscription: s.subscription ? { ...s.subscription, status } : null,
        }));

      const isLive = () => get().mode === "live";

      // ---- local-mode invoice/charge machinery (unchanged demo behaviour) ----
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
          idempotency_key: `charge_${sub.id}_${period(inv.period_start)}_${n}`,
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

      // provision a VA + transfer request (used by both modes on hard decline)
      const provisionTransfer = (amount: number, invoiceRef: string) => {
        const va = "8" + Math.floor(100000000 + Math.random() * 899999999);
        set((s) => ({
          customer: s.customer
            ? { ...s.customer, va_account_no: va, va_bank: "Nomba MFB" }
            : null,
          transfer: {
            account_no: va,
            bank: "Nomba MFB",
            amount,
            reference: invoiceRef.toUpperCase(),
            invoice_id: invoiceRef,
          },
        }));
        emit(
          "transfer.requested",
          `Transfer of ${formatKobo(amount)} requested to dedicated account`,
          { account_no: va, amount },
        );
      };

      const currentAmount = () => {
        const plan = planById(get().subscription?.plan_id);
        return plan?.amount ?? 0;
      };

      return {
        mode: "loading",
        syncing: false,
        error: null,
        apiPlans: [],
        realIdToTier: {},
        subscriptionId: null,
        customerId: null,
        localCard: null,
        lastProration: null,

        customer: null,
        subscription: null,
        invoices: [],
        charges: [],
        simEvents: [],
        liveEvents: [],
        events: [],
        transfer: null,
        selectedPlanId: null,

        bootstrap: async () => {
          try {
            const cfg = await api.config();
            if (!cfg.live) {
              set({ mode: "local" });
              rebuildFeed();
              return;
            }
            const { plans } = await api.plans();
            const realIdToTier: Record<number, Tier> = {};
            plans.forEach((p) => (realIdToTier[p.id] = p.tier));
            set({ mode: "live", apiPlans: plans, realIdToTier });

            const { subscriptionId } = get();
            if (subscriptionId) {
              await get().refresh();
            } else {
              // clear any stale local-mode membership so live starts clean
              set({
                subscription: null,
                customer: null,
                invoices: [],
                charges: [],
                simEvents: [],
                liveEvents: [],
                transfer: null,
              });
              rebuildFeed();
            }
          } catch (e) {
            set({
              mode: "local",
              error: e instanceof Error ? e.message : "Could not reach Somba",
            });
            rebuildFeed();
          }
        },

        refresh: async () => {
          if (get().mode !== "live" || !get().subscriptionId) return;
          set({ syncing: true, error: null });
          try {
            const id = get().subscriptionId!;
            const [subRes, invRes, evtRes] = await Promise.all([
              api.subscription(id, get().customerId ?? undefined),
              api.invoices(id),
              api.events(),
            ]);
            const realIdToTier = get().realIdToTier;
            set({
              subscription: mapSub(subRes.subscription, realIdToTier),
              customer: subRes.customer
                ? mapCustomer(subRes.customer, get().localCard)
                : get().customer,
              invoices: invRes.invoices.map(mapInvoice),
              liveEvents: evtRes.events
                .sort((a, b) => b.id - a.id)
                .map(mapLiveEvent),
            });
            rebuildFeed();
          } catch (e) {
            set({ error: e instanceof Error ? e.message : "Sync failed" });
          } finally {
            set({ syncing: false });
          }
        },

        selectPlan: (id) => set({ selectedPlanId: id }),

        signup: async ({ name, email, cardLast4, cardBrand, planId }) => {
          const card = { last4: cardLast4, brand: cardBrand };
          if (isLive()) {
            set({ syncing: true, error: null });
            try {
              const tier = tierOf(planId);
              const res = await api.subscribe({ name, email, tier });
              const realIdToTier = get().realIdToTier;
              set({
                subscriptionId: res.subscription.id,
                customerId: res.customer.id,
                localCard: card,
                subscription: mapSub(res.subscription, realIdToTier),
                customer: mapCustomer(res.customer, card),
                invoices: [],
                charges: [],
                simEvents: [],
                transfer: null,
                lastProration: null,
              });
              const { events } = await api.events();
              set({
                liveEvents: events.sort((a, b) => b.id - a.id).map(mapLiveEvent),
              });
              rebuildFeed();
            } catch (e) {
              set({ error: e instanceof Error ? e.message : "Sign-up failed" });
              throw e;
            } finally {
              set({ syncing: false });
            }
            return;
          }

          // ---- local mock mode ----
          const plan = planById(planId);
          if (!plan) return;
          const start = now();
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
            customer: {
              id: uid("cus"),
              name,
              email,
              card_last4: cardLast4,
              card_brand: cardBrand,
              va_account_no: null,
              va_bank: null,
              credit_balance: 0,
            },
            subscription: sub,
            invoices: [],
            charges: [],
            transfer: null,
            simEvents: [],
            liveEvents: [],
          });
          rebuildFeed();
          emit(
            "subscription.created",
            `${name} subscribed to ${plan.name}${trialing ? ` — ${plan.trial_days}-day trial` : ""}`,
            { subscription_id: sub.id, plan: plan.name, status: sub.status },
          );
          if (!trialing) {
            const inv = newInvoice(sub, plan.amount);
            recordCharge(sub, inv, "succeeded");
            settle(inv.id);
            emit("charge.succeeded", `First charge of ${formatKobo(plan.amount)} succeeded`, { invoice_id: inv.id });
            emit("subscription.active", "Membership is now active", { subscription_id: sub.id });
          }
        },

        activateFromTrial: () => {
          const { subscription } = get();
          if (!subscription || subscription.status !== "trialing") return;
          if (isLive()) {
            setStatus("active");
            emit("charge.succeeded", "Trial converted — first charge succeeded (simulated)", {});
            emit("subscription.active", "Membership active (simulated)", {});
            return;
          }
          const plan = planById(subscription.plan_id)!;
          const inv = newInvoice(subscription, plan.amount);
          recordCharge(subscription, inv, "succeeded");
          settle(inv.id);
          setStatus("active");
          emit("charge.succeeded", `First charge of ${formatKobo(plan.amount)} succeeded`, { invoice_id: inv.id });
          emit("subscription.active", "Trial converted — membership active", { subscription_id: subscription.id });
        },

        renew: () => {
          const { subscription } = get();
          if (!subscription) return;
          if (isLive()) {
            setStatus("active");
            emit("charge.succeeded", `Renewal of ${formatKobo(currentAmount())} succeeded (simulated)`, {});
            emit("subscription.active", "Membership renewed (simulated)", {});
            return;
          }
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
          emit("charge.succeeded", `Renewal of ${formatKobo(plan.amount)} succeeded`, { invoice_id: inv.id });
          emit("subscription.active", "Membership renewed for another month", { subscription_id: next.id });
        },

        triggerFailure: (failureClass) => {
          const { subscription, customer } = get();
          if (!subscription || !customer) return;
          const copy = FAILURE_COPY[failureClass];
          const amount = currentAmount();

          if (isLive()) {
            emit("charge.failed", `Charge failed — ${copy.nomba} (simulated)`, { failure_class: failureClass });
            if (failureClass === "risk") {
              setStatus("past_due");
              emit("anomaly.detected", "Risk block — merchant notified, retries stopped", {});
              emit("subscription.past_due", "Membership is past due", {});
              return;
            }
            if (failureClass === "broken_card") {
              provisionTransfer(amount, uid("in"));
              setStatus("past_due");
              emit("subscription.past_due", "Past due — transfer requested", {});
              return;
            }
            setStatus("past_due");
            emit("subscription.past_due", "Past due — retry scheduled for a funding window", {});
            return;
          }

          const plan = planById(subscription.plan_id)!;
          const inv = newInvoice(subscription, plan.amount);
          recordCharge(subscription, inv, "failed", { failure_class: failureClass, failure_reason: copy.nomba });
          emit("charge.failed", `Charge failed — ${copy.nomba}`, { invoice_id: inv.id, failure_class: failureClass });

          if (failureClass === "risk") {
            setStatus("past_due");
            emit("anomaly.detected", "Risk block — merchant notified, retries stopped", { subscription_id: subscription.id });
            emit("subscription.past_due", "Membership is past due", { subscription_id: subscription.id });
            return;
          }
          if (failureClass === "broken_card") {
            provisionTransfer(inv.amount, inv.id);
            setStatus("past_due");
            emit("subscription.past_due", "Membership is past due — transfer requested", { subscription_id: subscription.id });
            return;
          }
          if (failureClass === "transient") {
            recordCharge(subscription, inv, "failed", { failure_class: failureClass, failure_reason: copy.nomba });
            emit("charge.retrying", "Soft decline — one immediate retry", { invoice_id: inv.id });
          }
          setStatus("past_due");
          emit("subscription.past_due", "Membership past due — retry scheduled for a funding window", { subscription_id: subscription.id });
        },

        triggerTimeout: () => {
          const { subscription } = get();
          if (!subscription) return;
          if (isLive()) {
            setStatus("payment_uncertain");
            emit("payment.uncertain", "Charge timed out — subscription frozen pending verify (simulated)", {});
            return;
          }
          const plan = planById(subscription.plan_id)!;
          const inv = newInvoice(subscription, plan.amount);
          recordCharge(subscription, inv, "uncertain", { failure_reason: "timeout_no_response" });
          setStatus("payment_uncertain");
          emit("payment.uncertain", "Charge timed out — subscription frozen pending verify", { invoice_id: inv.id, subscription_id: subscription.id });
        },

        retryPayment: () => {
          const { subscription, invoices } = get();
          if (!subscription || subscription.status !== "past_due") return;
          if (isLive()) {
            setStatus("active");
            set({ transfer: null });
            emit("charge.recovered", "Retry succeeded — payment recovered (simulated)", {});
            emit("subscription.active", "Membership healed back to active (simulated)", {});
            return;
          }
          const open = invoices.find((i) => i.status === "open");
          if (!open) return;
          recordCharge(subscription, open, "succeeded");
          settle(open.id);
          setStatus("active");
          set({ transfer: null });
          emit("charge.recovered", "Retry succeeded — payment recovered", { invoice_id: open.id });
          emit("subscription.active", "Membership healed back to active", { subscription_id: subscription.id });
        },

        simulateTransferPush: () => {
          const { subscription, transfer } = get();
          if (!subscription || !transfer) return;
          if (!isLive()) settle(transfer.invoice_id);
          setStatus("active");
          set({ transfer: null });
          emit("transfer.reconciled", `Transfer of ${formatKobo(transfer.amount)} matched to open invoice`, { amount: transfer.amount });
          emit("charge.recovered", "Payment recovered via transfer fallback", {});
          emit("subscription.active", "Membership healed back to active", { subscription_id: subscription.id });
        },

        resolveUncertain: (succeeded) => {
          const { subscription, invoices } = get();
          if (!subscription || subscription.status !== "payment_uncertain") return;
          const open = invoices.find((i) => i.status === "open");
          if (succeeded) {
            if (open && !isLive()) settle(open.id);
            setStatus("active");
            emit("payment.resolved", "Verify pass confirmed success", { subscription_id: subscription.id });
            emit("subscription.active", "Membership healed back to active", { subscription_id: subscription.id });
          } else {
            setStatus("past_due");
            emit("payment.resolved", "Verify pass confirmed failure", { subscription_id: subscription.id });
            emit("subscription.past_due", "Now in recovery — verified failure", { subscription_id: subscription.id });
          }
        },

        pause: () => {
          const { subscription } = get();
          if (!subscription) return;
          setStatus("paused");
          emit("subscription.paused", "Membership paused — no billing runs", { subscription_id: subscription.id });
        },

        resume: () => {
          const { subscription } = get();
          if (!subscription) return;
          setStatus("active");
          emit("subscription.resumed", "Membership resumed", { subscription_id: subscription.id });
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
          emit("subscription.cancelled", "Membership cancelled — no further billing", { subscription_id: subscription.id });
        },

        changePlan: async (newPlanId) => {
          const { subscription, customer } = get();
          if (!subscription || !customer) return;
          const oldPlan = planById(subscription.plan_id)!;
          const newPlan = planById(newPlanId)!;
          if (oldPlan.id === newPlan.id) return;

          if (isLive() && get().subscriptionId) {
            set({ syncing: true, error: null });
            try {
              const res = await api.changePlan(get().subscriptionId!, tierOf(newPlanId));
              set({
                subscription: mapSub(res.subscription, get().realIdToTier),
                lastProration: res.proration,
              });
              const { events } = await api.events();
              set({ liveEvents: events.sort((a, b) => b.id - a.id).map(mapLiveEvent) });
              rebuildFeed();
            } catch (e) {
              set({ error: e instanceof Error ? e.message : "Plan change failed" });
              throw e;
            } finally {
              set({ syncing: false });
            }
            return;
          }

          // ---- local proration ----
          const daysInPeriod = 30;
          const msLeft = new Date(subscription.current_period_end).getTime() - Date.now();
          const daysRemaining = Math.max(0, Math.min(daysInPeriod, Math.round(msLeft / 86_400_000)));
          const { credit, charge, net } = prorate(oldPlan.amount, newPlan.amount, daysInPeriod, daysRemaining);
          set((s) => ({
            subscription: s.subscription ? { ...s.subscription, plan_id: newPlan.id } : null,
          }));
          emit("subscription.updated", `Plan changed: ${oldPlan.name} → ${newPlan.name}`, { credit, charge, net, days_remaining: daysRemaining });
          if (net > 0) {
            const sub = get().subscription!;
            const inv = newInvoice(sub, net, "proration");
            recordCharge(sub, inv, "succeeded");
            settle(inv.id);
            emit("charge.succeeded", `Proration charge of ${formatKobo(net)} succeeded`, { invoice_id: inv.id });
          } else if (net < 0) {
            set((s) => ({
              customer: s.customer ? { ...s.customer, credit_balance: s.customer.credit_balance - net } : null,
            }));
            emit("subscription.updated", `Downgrade credit of ${formatKobo(-net)} banked for next renewal`, { credit: -net });
          }
        },

        updateCard: (last4, brand) => {
          set((s) => ({
            customer: s.customer ? { ...s.customer, card_last4: last4, card_brand: brand } : null,
            localCard: { last4, brand },
          }));
          const { subscription } = get();
          if (subscription) emit("subscription.updated", `Card updated — now •••• ${last4}`, { subscription_id: subscription.id });
        },

        reset: () => {
          set({
            customer: null,
            subscription: null,
            invoices: [],
            charges: [],
            simEvents: [],
            liveEvents: [],
            events: [],
            transfer: null,
            selectedPlanId: null,
            subscriptionId: null,
            customerId: null,
            localCard: null,
            lastProration: null,
          });
        },
      };
    },
    {
      name: "gymflow-demo-v2",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({
        customer: s.customer,
        subscription: s.subscription,
        invoices: s.invoices,
        charges: s.charges,
        simEvents: s.simEvents,
        transfer: s.transfer,
        selectedPlanId: s.selectedPlanId,
        subscriptionId: s.subscriptionId,
        customerId: s.customerId,
        localCard: s.localCard,
        lastProration: s.lastProration,
      }),
    },
  ),
);

/** Avoids hydration mismatch: true only after the persisted store mounts. */
export function useHydrated(): boolean {
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => setHydrated(true), []);
  return hydrated;
}
