"use client";

// Client-side API — talks only to our own /api/somba/* proxy (never the live
// API directly, so the merchant key stays on the server).

export type Tier = "basic" | "standard" | "premium";

export interface ApiSubscription {
  id: number;
  merchant_id: number;
  customer_id: number;
  plan_id: number;
  status: string;
  current_period_start: string | null;
  current_period_end: string | null;
  next_bill_date: string | null;
  trial_end: string | null;
  cancel_at_period_end: boolean;
  cancelled_at: string | null;
}

export interface ApiCustomer {
  id: number;
  merchant_id: number;
  external_id: string | null;
  email: string | null;
  name: string | null;
  va_account_no: string | null;
  credit_balance: number;
}

export interface ApiInvoice {
  id: number;
  subscription_id: number;
  customer_id: number;
  amount: number;
  status: string;
  type: string;
  period_start: string | null;
  period_end: string | null;
  due_date: string | null;
  paid_at: string | null;
}

export interface ApiEvent {
  id: number;
  event_type: string;
  aggregate_type: string;
  aggregate_id: string;
  payload: Record<string, unknown>;
  status: string;
}

export interface ApiPlan {
  tier: Tier;
  id: number;
  name: string;
  amount: number;
  currency: string;
  interval: string;
  interval_count: number;
  trial_days: number;
  status: string;
}

export interface ApiProration {
  action: string;
  credit_kobo: number;
  charge_kobo: number;
  net_kobo: number;
  remaining_days: number;
  total_days: number;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path, { cache: "no-store" });
  const json = await res.json();
  if (!res.ok) throw new Error(json?.error?.message ?? "Request failed");
  return json as T;
}

async function send<T>(path: string, method: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json?.error?.message ?? "Request failed");
  return json as T;
}

export const api = {
  config: () => get<{ live: boolean; base: string }>("/api/somba/config"),
  plans: () => get<{ plans: ApiPlan[] }>("/api/somba/plans"),
  subscribe: (body: { name: string; email: string; tier: Tier }) =>
    send<{
      subscription: ApiSubscription;
      customer: ApiCustomer;
      tier: Tier;
      plan: ApiPlan;
    }>("/api/somba/subscribe", "POST", body),
  subscription: (id: number, customerId?: number) =>
    get<{ subscription: ApiSubscription; customer: ApiCustomer | null }>(
      `/api/somba/subscription?id=${id}${customerId ? `&customer_id=${customerId}` : ""}`,
    ),
  changePlan: (id: number, tier: Tier) =>
    send<{ subscription: ApiSubscription; proration: ApiProration; tier: Tier }>(
      "/api/somba/subscription",
      "PATCH",
      { id, tier },
    ),
  invoices: (subscriptionId: number) =>
    get<{ invoices: ApiInvoice[] }>(
      `/api/somba/invoices?subscription_id=${subscriptionId}`,
    ),
  events: () => get<{ events: ApiEvent[] }>("/api/somba/events"),
};
