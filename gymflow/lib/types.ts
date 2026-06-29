// Types mirror Somba's API/data model so the mock can be swapped for the real
// API later by changing only the data source, not the screens.

export type SubscriptionStatus =
  | "trialing"
  | "active"
  | "past_due"
  | "payment_uncertain"
  | "paused"
  | "cancelled"
  | "expired";

export type InvoiceStatus = "draft" | "open" | "paid" | "void" | "uncollectible";

export type FailureClass =
  | "empty_account"
  | "broken_card"
  | "transient"
  | "risk"
  | "unknown";

export type ChargeStatus = "pending" | "succeeded" | "failed" | "uncertain";

export interface Plan {
  id: string;
  name: string;
  tagline: string;
  amount: number; // kobo
  currency: "NGN";
  interval: "month";
  trial_days: number;
  perks: string[];
  featured?: boolean;
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  card_last4: string;
  card_brand: string;
  va_account_no: string | null;
  va_bank: string | null;
  credit_balance: number; // kobo
}

export interface Subscription {
  id: string;
  plan_id: string;
  status: SubscriptionStatus;
  current_period_start: string; // ISO
  current_period_end: string; // ISO
  next_bill_date: string; // ISO
  trial_end: string | null;
  created_at: string;
}

export interface Invoice {
  id: string;
  subscription_id: string;
  amount: number; // kobo
  status: InvoiceStatus;
  type: "regular" | "proration";
  period_start: string;
  period_end: string;
  created_at: string;
  paid_at: string | null;
}

export interface ChargeAttempt {
  id: string;
  invoice_id: string;
  idempotency_key: string;
  order_reference: string;
  amount: number;
  status: ChargeStatus;
  failure_reason: string | null;
  failure_class: FailureClass | null;
  attempt_number: number;
  created_at: string;
}

export type WebhookEventType =
  | "subscription.created"
  | "invoice.created"
  | "charge.succeeded"
  | "charge.failed"
  | "charge.retrying"
  | "charge.recovered"
  | "transfer.requested"
  | "transfer.reconciled"
  | "subscription.past_due"
  | "subscription.active"
  | "subscription.paused"
  | "subscription.resumed"
  | "subscription.cancelled"
  | "subscription.updated"
  | "payment.uncertain"
  | "payment.resolved"
  | "anomaly.detected";

export interface WebhookEvent {
  id: string;
  type: WebhookEventType;
  summary: string;
  created_at: string;
  delivered: boolean;
  signature: string; // fake hmac for the demo
  payload: Record<string, unknown>;
}

export interface TransferRequest {
  account_no: string;
  bank: string;
  amount: number; // kobo
  reference: string;
  invoice_id: string;
}
