"use client";

import { useState } from "react";
import { useDemo } from "@/lib/store";
import { planById } from "@/lib/plans";
import { naira } from "@/lib/money";
import { fmtDate, relativeDays } from "@/lib/format";
import { STATE_META } from "@/lib/states";
import { MembershipCard } from "@/components/MembershipCard";
import { LifecycleRail } from "@/components/LifecycleRail";
import { StateBadge } from "@/components/StateBadge";
import { DemoControls } from "@/components/DemoControls";
import { ChangePlanDialog } from "@/components/ChangePlanDialog";
import { Button, ButtonLink, Card } from "@/components/ui";

export default function MembershipPage() {
  const sub = useDemo((s) => s.subscription)!;
  const customer = useDemo((s) => s.customer)!;
  const pause = useDemo((s) => s.pause);
  const resume = useDemo((s) => s.resume);
  const cancel = useDemo((s) => s.cancel);
  const [showChange, setShowChange] = useState(false);
  const [confirmCancel, setConfirmCancel] = useState(false);

  const plan = planById(sub.plan_id);
  const meta = STATE_META[sub.status];
  const firstName = customer.name.split(" ")[0];
  const manageable = ["active", "trialing", "past_due", "paused"].includes(
    sub.status,
  );

  return (
    <div className="mx-auto max-w-6xl px-5 py-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="kicker text-smoke">Membership</p>
          <h1 className="display text-4xl md:text-5xl mt-2">
            Welcome back, {firstName}.
          </h1>
        </div>
        <StateBadge status={sub.status} size="lg" />
      </div>

      <div className="mt-8 grid lg:grid-cols-[0.95fr_1.05fr] gap-6 items-start">
        {/* left: the pass + facts */}
        <div className="space-y-6">
          <div className="rounded-2xl bg-ink p-6 flex justify-center">
            <MembershipCard
              customer={{ name: customer.name, card_last4: customer.card_last4 }}
              plan={plan}
              status={sub.status}
              memberId={sub.id.toUpperCase()}
            />
          </div>

          <Card className="p-5">
            <dl className="grid grid-cols-2 gap-x-4 gap-y-5">
              <Fact label="Plan" value={plan?.name ?? "—"} />
              <Fact
                label="Price"
                value={plan ? `${naira(plan.amount)}/mo` : "—"}
              />
              <Fact
                label={sub.status === "trialing" ? "Trial ends" : "Next bill"}
                value={
                  sub.status === "cancelled" || sub.status === "expired"
                    ? "—"
                    : fmtDate(
                        sub.status === "trialing"
                          ? sub.trial_end
                          : sub.next_bill_date,
                      )
                }
                sub={
                  sub.status === "cancelled" || sub.status === "expired"
                    ? undefined
                    : relativeDays(
                        sub.status === "trialing"
                          ? sub.trial_end
                          : sub.next_bill_date,
                      )
                }
              />
              <Fact
                label="Current period"
                value={`${fmtDate(sub.current_period_start)} – ${fmtDate(sub.current_period_end)}`}
              />
              <Fact
                label="Payment method"
                value={`${customer.card_brand} •••• ${customer.card_last4}`}
              />
              {customer.credit_balance > 0 ? (
                <Fact
                  label="Account credit"
                  value={naira(customer.credit_balance)}
                  highlight
                />
              ) : (
                <Fact label="Member since" value={fmtDate(sub.created_at)} />
              )}
            </dl>
          </Card>
        </div>

        {/* right: status + lifecycle + manage */}
        <div className="space-y-6">
          {/* status callout */}
          <StatusCallout />

          <Card className="p-5">
            <p className="kicker text-smoke mb-4">Where you are in the lifecycle</p>
            <LifecycleRail current={sub.status} />
            <p className="mt-4 text-sm text-smoke">{meta.plain}</p>
          </Card>

          {/* manage */}
          {manageable && (
            <Card className="p-5">
              <p className="kicker text-smoke mb-4">Manage membership</p>
              <div className="flex flex-wrap gap-2.5">
                <Button variant="outline" onClick={() => setShowChange(true)}>
                  Change plan
                </Button>
                {sub.status === "paused" ? (
                  <Button variant="primary" onClick={resume}>
                    Resume
                  </Button>
                ) : (
                  <Button variant="ghost" onClick={pause}>
                    Pause billing
                  </Button>
                )}
                {confirmCancel ? (
                  <Button variant="danger" onClick={cancel}>
                    Confirm cancel
                  </Button>
                ) : (
                  <Button
                    variant="ghost"
                    onClick={() => setConfirmCancel(true)}
                    className="!text-smoke hover:!text-danger"
                  >
                    Cancel membership
                  </Button>
                )}
              </div>
            </Card>
          )}
        </div>
      </div>

      <div className="mt-8">
        <DemoControls status={sub.status} />
      </div>

      {showChange && <ChangePlanDialog onClose={() => setShowChange(false)} />}
    </div>
  );
}

function Fact({
  label,
  value,
  sub,
  highlight,
}: {
  label: string;
  value: string;
  sub?: string;
  highlight?: boolean;
}) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-smoke-2">
        {label}
      </dt>
      <dd
        className={`mt-1 font-semibold ${highlight ? "text-volt-deep" : "text-ink"}`}
      >
        {value}
      </dd>
      {sub && <dd className="text-xs text-smoke-2 mt-0.5">{sub}</dd>}
    </div>
  );
}

function StatusCallout() {
  const sub = useDemo((s) => s.subscription)!;
  const transfer = useDemo((s) => s.transfer);

  switch (sub.status) {
    case "active":
      return (
        <Callout tone="good" title="You're all set.">
          Everything&apos;s open to you. Your card is charged automatically each
          month — nothing to do.
        </Callout>
      );
    case "trialing":
      return (
        <Callout tone="good" title="You're on a free trial.">
          No charge yet. Your first payment runs when the trial ends. Cancel
          before then and you won&apos;t be billed.
        </Callout>
      );
    case "past_due":
      return (
        <Callout tone="warn" title="A payment didn't go through.">
          You still have full access while we recover it.{" "}
          {transfer
            ? "We've sent you a transfer request — finish it to heal your pass instantly."
            : "We'll retry automatically at a better time."}
          <div className="mt-3">
            <ButtonLink href="/membership/recovery" variant="dark">
              Open recovery
            </ButtonLink>
          </div>
        </Callout>
      );
    case "payment_uncertain":
      return (
        <Callout tone="frozen" title="We're confirming a payment.">
          Your last charge timed out, so we&apos;ve frozen billing rather than
          guess. A verify pass settles the truth within minutes — no double
          charges, ever.
        </Callout>
      );
    case "paused":
      return (
        <Callout tone="rest" title="Membership paused.">
          No billing runs while you&apos;re paused. Resume whenever you&apos;re
          ready and you&apos;ll pick up right where you left off.
        </Callout>
      );
    case "cancelled":
      return (
        <Callout tone="rest" title="Membership cancelled.">
          No further billing. We&apos;d love to have you back — start a new
          membership any time.
          <div className="mt-3">
            <ButtonLink href="/" variant="dark">
              Rejoin GymFlow
            </ButtonLink>
          </div>
        </Callout>
      );
    default:
      return (
        <Callout tone="rest" title="Membership ended.">
          This membership reached its natural end.
        </Callout>
      );
  }
}

function Callout({
  tone,
  title,
  children,
}: {
  tone: "good" | "warn" | "frozen" | "rest";
  title: string;
  children: React.ReactNode;
}) {
  const ring =
    tone === "good"
      ? "border-l-volt"
      : tone === "warn"
        ? "border-l-due"
        : tone === "frozen"
          ? "border-l-frozen"
          : "border-l-rest";
  return (
    <Card className={`p-5 border-l-4 ${ring}`}>
      <h2 className="display text-2xl">{title}</h2>
      <div className="mt-2 text-sm text-smoke leading-relaxed">{children}</div>
    </Card>
  );
}
