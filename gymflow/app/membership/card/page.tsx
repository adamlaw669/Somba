"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useDemo } from "@/lib/store";
import { Button, Card, Field, inputCls } from "@/components/ui";

function detectBrand(num: string): string {
  if (num.startsWith("4")) return "Visa";
  if (/^5[1-5]/.test(num)) return "Mastercard";
  if (num.startsWith("5061") || num.startsWith("650")) return "Verve";
  return "Card";
}

export default function CardPortal() {
  const router = useRouter();
  const customer = useDemo((s) => s.customer)!;
  const sub = useDemo((s) => s.subscription)!;
  const updateCard = useDemo((s) => s.updateCard);
  const retryPayment = useDemo((s) => s.retryPayment);

  const [card, setCard] = useState("");
  const [exp, setExp] = useState("");
  const [cvc, setCvc] = useState("");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);

  const digits = card.replace(/\D/g, "");
  const valid =
    digits.length >= 15 && /^\d{2}\/\d{2}$/.test(exp) && cvc.length >= 3;
  const pastDue = sub.status === "past_due";

  const onCardChange = (v: string) =>
    setCard(
      v
        .replace(/\D/g, "")
        .slice(0, 16)
        .replace(/(.{4})/g, "$1 ")
        .trim(),
    );
  const onExpChange = (v: string) => {
    const d = v.replace(/\D/g, "").slice(0, 4);
    setExp(d.length > 2 ? `${d.slice(0, 2)}/${d.slice(2)}` : d);
  };

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!valid) return;
    setBusy(true);
    await new Promise((r) => setTimeout(r, 800));
    updateCard(digits.slice(-4), detectBrand(digits));
    setBusy(false);
    setSaved(true);
    setCard("");
    setExp("");
    setCvc("");
    setTimeout(() => setSaved(false), 2500);
  };

  const saveAndRetry = async (e: React.FormEvent) => {
    await save(e);
    retryPayment();
    router.push("/membership");
  };

  return (
    <div className="mx-auto max-w-2xl px-5 py-10">
      <p className="kicker text-smoke">Billing</p>
      <h1 className="display text-4xl md:text-5xl mt-2">Payment method</h1>
      <p className="mt-3 text-smoke">
        Update the card we charge each month. It&apos;s tokenised on this device —
        we only keep a token and the last four digits.
      </p>

      {pastDue && (
        <Card className="mt-6 p-5 border-l-4 border-l-due">
          <h2 className="display text-xl">A payment is waiting to be recovered</h2>
          <p className="mt-1.5 text-sm text-smoke">
            Update your card and we&apos;ll retry straight away, or retry the
            current card as-is.
          </p>
        </Card>
      )}

      <Card className="mt-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-smoke-2">
              Current card
            </p>
            <p className="mt-1 font-semibold text-lg">
              {customer.card_brand}{" "}
              <span className="mono">•••• {customer.card_last4}</span>
            </p>
          </div>
          <div className="h-8 w-12 rounded-md bg-gradient-to-br from-volt to-volt-deep" />
        </div>
      </Card>

      <form onSubmit={pastDue ? saveAndRetry : save} className="mt-6">
        <Card className="p-6 space-y-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-smoke">
            New card
          </p>
          <Field label="Card number">
            <input
              className={`${inputCls} mono`}
              value={card}
              onChange={(e) => onCardChange(e.target.value)}
              placeholder="4242 4242 4242 4242"
              inputMode="numeric"
            />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Expiry">
              <input
                className={`${inputCls} mono`}
                value={exp}
                onChange={(e) => onExpChange(e.target.value)}
                placeholder="08/28"
                inputMode="numeric"
              />
            </Field>
            <Field label="CVC">
              <input
                className={`${inputCls} mono`}
                value={cvc}
                onChange={(e) =>
                  setCvc(e.target.value.replace(/\D/g, "").slice(0, 4))
                }
                placeholder="123"
                inputMode="numeric"
              />
            </Field>
          </div>
        </Card>

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <Button type="submit" variant="primary" disabled={busy || !valid}>
            {busy
              ? "Saving…"
              : pastDue
                ? "Save card & retry payment"
                : "Save card"}
          </Button>
          {pastDue && (
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                retryPayment();
                router.push("/membership");
              }}
            >
              Retry current card
            </Button>
          )}
          {saved && (
            <span className="text-sm font-semibold text-volt-deep">
              ✓ Card updated
            </span>
          )}
        </div>
      </form>

      {customer.va_account_no && (
        <Card className="mt-8 p-5 bg-concrete">
          <p className="kicker text-smoke">Prefer to transfer?</p>
          <p className="mt-2 text-sm text-smoke">
            You have a dedicated account on file. See it on the{" "}
            <a
              href="/membership/recovery"
              className="text-ink font-semibold underline-offset-2 hover:underline"
            >
              recovery page
            </a>
            .
          </p>
        </Card>
      )}
    </div>
  );
}
