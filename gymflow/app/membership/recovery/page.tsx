"use client";

import { useState } from "react";
import { useDemo } from "@/lib/store";
import { naira } from "@/lib/money";
import type { FailureClass } from "@/lib/types";
import { Button, ButtonLink, Card } from "@/components/ui";

const REASON: Record<
  FailureClass,
  { title: string; plain: string; path: string }
> = {
  empty_account: {
    title: "Your account was empty when we tried",
    plain:
      "The card is fine — there just wasn't enough in the account at that moment. This is the most common reason payments slip in Nigeria.",
    path: "We'll retry automatically near a funding window — like just after payday. You keep full access while we wait.",
  },
  broken_card: {
    title: "Your card was declined",
    plain:
      "The bank turned this card down for good — it may be expired or blocked. Pulling again won't help.",
    path: "We've switched to a transfer instead. Send the amount below and your pass heals the moment it lands.",
  },
  transient: {
    title: "Your bank asked us to try again later",
    plain:
      "A temporary soft decline — nothing wrong on your end. We already retried once.",
    path: "We'll retry once more at a better time. You can also retry now or update your card.",
  },
  risk: {
    title: "Your bank flagged this payment",
    plain:
      "For your safety, the bank blocked the charge. We've stopped trying and notified the gym.",
    path: "Please check with your bank, then update your card to continue.",
  },
  unknown: {
    title: "We couldn't get a clear answer",
    plain: "The result wasn't certain, so we won't guess.",
    path: "We'll recover safely and fall back to a transfer if needed.",
  },
};

export default function RecoveryPage() {
  const sub = useDemo((s) => s.subscription)!;
  const charges = useDemo((s) => s.charges);
  const transfer = useDemo((s) => s.transfer);
  const retryPayment = useDemo((s) => s.retryPayment);
  const simulateTransferPush = useDemo((s) => s.simulateTransferPush);
  const resolveUncertain = useDemo((s) => s.resolveUncertain);

  // healthy states — nothing to recover
  if (sub.status !== "past_due" && sub.status !== "payment_uncertain") {
    return (
      <div className="mx-auto max-w-3xl px-5 py-16 text-center">
        <div className="inline-flex h-14 w-14 items-center justify-center rounded-full bg-volt text-ink display text-2xl">
          ✓
        </div>
        <h1 className="display text-4xl mt-5">Nothing to recover</h1>
        <p className="mt-3 text-smoke max-w-md mx-auto">
          Your membership is healthy. If a payment ever slips, this is where
          you&apos;ll find a clear explanation and a one-tap way to fix it.
        </p>
        <div className="mt-7">
          <ButtonLink href="/membership" variant="dark">
            Back to membership
          </ButtonLink>
        </div>
      </div>
    );
  }

  // payment_uncertain — frozen, verifying
  if (sub.status === "payment_uncertain") {
    return (
      <div className="mx-auto max-w-3xl px-5 py-10">
        <p className="kicker text-frozen">Verifying payment</p>
        <h1 className="display text-4xl md:text-5xl mt-2">
          We&apos;re confirming your last payment
        </h1>
        <Card className="mt-7 p-6 border-l-4 border-l-frozen">
          <p className="text-smoke leading-relaxed">
            Your charge timed out before the bank confirmed it. Rather than risk
            charging you twice, we&apos;ve <strong>frozen</strong> your billing
            and started a verify pass. It checks directly with the bank using the
            original reference and settles the truth — usually within five
            minutes.
          </p>
          <div className="mt-5 flex items-center gap-3 text-sm text-frozen">
            <span className="h-2 w-2 rounded-full bg-frozen live-dot" />
            Verify pass running…
          </div>
        </Card>

        <div className="mt-6 rounded-2xl bg-ink text-paper p-5 border-2 border-dashed border-ink-3">
          <p className="kicker text-volt mb-3">Demo: settle the verify pass</p>
          <div className="flex flex-wrap gap-2.5">
            <Button variant="primary" onClick={() => resolveUncertain(true)}>
              It succeeded → heal
            </Button>
            <Button
              variant="outline"
              className="!border-paper/30 !text-paper hover:!bg-paper hover:!text-ink"
              onClick={() => resolveUncertain(false)}
            >
              It failed → recover
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // past_due — show the reason + recovery path
  const lastFailed = charges.find((c) => c.status === "failed");
  const cls: FailureClass = lastFailed?.failure_class ?? "unknown";
  const reason = REASON[cls];
  const amountDue = transfer?.amount ?? lastFailed?.amount ?? 0;

  return (
    <div className="mx-auto max-w-3xl px-5 py-10">
      <p className="kicker text-due">Recovery · you still have access</p>
      <h1 className="display text-4xl md:text-5xl mt-2">{reason.title}</h1>

      <Card className="mt-7 p-6 border-l-4 border-l-due">
        <p className="text-smoke leading-relaxed">{reason.plain}</p>
        <div className="mt-4 pt-4 border-t border-concrete-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-smoke-2">
            What happens next
          </p>
          <p className="mt-1.5 text-ink">{reason.path}</p>
        </div>
      </Card>

      {/* transfer fallback */}
      {transfer ? (
        <TransferFallback
          accountNo={transfer.account_no}
          bank={transfer.bank}
          amount={transfer.amount}
          reference={transfer.reference}
          onSent={simulateTransferPush}
        />
      ) : (
        <Card className="mt-6 p-6">
          <p className="kicker text-smoke mb-3">Fix it faster</p>
          <div className="flex flex-wrap gap-2.5">
            <Button variant="primary" onClick={retryPayment}>
              Retry payment now
            </Button>
            <ButtonLink href="/membership/card" variant="outline">
              Update card
            </ButtonLink>
          </div>
          <p className="mt-3 text-xs text-smoke-2">
            Amount due: {naira(amountDue)} · We&apos;ll also retry on our own at a
            better time.
          </p>
        </Card>
      )}
    </div>
  );
}

function TransferFallback({
  accountNo,
  bank,
  amount,
  reference,
  onSent,
}: {
  accountNo: string;
  bank: string;
  amount: number;
  reference: string;
  onSent: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(accountNo);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard blocked — number is visible anyway */
    }
  };

  return (
    <div className="mt-6 rounded-2xl bg-ink text-paper overflow-hidden">
      <div className="hazard-thin h-2" />
      <div className="p-6">
        <p className="kicker text-volt">Transfer fallback</p>
        <h2 className="display text-2xl mt-2">
          Send a transfer to heal your pass
        </h2>
        <p className="mt-2 text-sm text-paper/60">
          This account is yours alone. The moment your transfer lands, we match it
          to your open invoice and flip you back to active — automatically.
        </p>

        <div className="mt-5 grid sm:grid-cols-2 gap-4">
          <Detail label="Send exactly">
            <span className="display text-3xl text-volt">{naira(amount)}</span>
          </Detail>
          <Detail label="Bank">
            <span className="text-lg font-semibold">{bank}</span>
          </Detail>
          <div className="sm:col-span-2">
            <Detail label="Account number">
              <div className="flex items-center gap-3">
                <span className="mono text-2xl tracking-wider">{accountNo}</span>
                <button
                  onClick={copy}
                  className="text-xs font-semibold uppercase tracking-wide bg-paper/10 hover:bg-volt hover:text-ink px-3 py-1.5 rounded-full transition-colors"
                >
                  {copied ? "Copied" : "Copy"}
                </button>
              </div>
            </Detail>
          </div>
          <div className="sm:col-span-2">
            <Detail label="Narration / reference">
              <span className="mono text-sm text-paper/80">{reference}</span>
            </Detail>
          </div>
        </div>

        <div className="mt-6 flex items-center gap-3 border-t border-ink-3 pt-5">
          <Button variant="primary" onClick={onSent}>
            I&apos;ve sent the transfer
          </Button>
          <span className="text-xs text-paper/50">
            (Demo) Simulates the transfer landing &amp; reconciling.
          </span>
        </div>
      </div>
    </div>
  );
}

function Detail({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl bg-ink-2 border border-ink-3 p-4">
      <p className="kicker text-paper/40">{label}</p>
      <div className="mt-1.5">{children}</div>
    </div>
  );
}
