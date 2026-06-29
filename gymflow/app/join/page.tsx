"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { PLANS, planById } from "@/lib/plans";
import { naira } from "@/lib/money";
import { useDemo, useHydrated } from "@/lib/store";
import { MembershipCard } from "@/components/MembershipCard";
import { Button, Field, inputCls } from "@/components/ui";

function detectBrand(num: string): string {
  const n = num.replace(/\s/g, "");
  if (n.startsWith("4")) return "Visa";
  if (/^5[1-5]/.test(n)) return "Mastercard";
  if (n.startsWith("5061") || n.startsWith("650")) return "Verve";
  return "Card";
}

export default function Join() {
  const router = useRouter();
  const hydrated = useHydrated();
  const selectedPlanId = useDemo((s) => s.selectedPlanId);
  const selectPlan = useDemo((s) => s.selectPlan);
  const signup = useDemo((s) => s.signup);

  const planId = (hydrated && selectedPlanId) || "plan_standard";
  const plan = planById(planId)!;

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [card, setCard] = useState("");
  const [exp, setExp] = useState("");
  const [cvc, setCvc] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const digits = card.replace(/\D/g, "");
  const valid =
    name.trim().length > 1 &&
    /\S+@\S+\.\S+/.test(email) &&
    digits.length >= 15 &&
    /^\d{2}\/\d{2}$/.test(exp) &&
    cvc.length >= 3;

  const onCardChange = (v: string) => {
    const d = v.replace(/\D/g, "").slice(0, 16);
    setCard(d.replace(/(.{4})/g, "$1 ").trim());
  };
  const onExpChange = (v: string) => {
    const d = v.replace(/\D/g, "").slice(0, 4);
    setExp(d.length > 2 ? `${d.slice(0, 2)}/${d.slice(2)}` : d);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!valid) {
      setError("Check your details — something's missing or mistyped.");
      return;
    }
    setError(null);
    setBusy(true);
    // simulate client-side card tokenisation (the raw PAN never leaves the form)
    await new Promise((r) => setTimeout(r, 900));
    signup({
      name: name.trim(),
      email: email.trim(),
      cardLast4: digits.slice(-4),
      cardBrand: detectBrand(digits),
      planId,
    });
    router.push("/membership");
  };

  return (
    <div className="min-h-screen flex flex-col bg-concrete">
      <header className="border-b border-concrete-2 bg-paper">
        <div className="mx-auto max-w-6xl px-5 h-16 flex items-center justify-between">
          <Link href="/" className="display text-ink text-2xl leading-none">
            Gym<span className="text-volt-deep">Flow</span>
          </Link>
          <Link
            href="/"
            className="text-sm font-semibold text-smoke hover:text-ink transition-colors"
          >
            ← Back to plans
          </Link>
        </div>
      </header>

      <main className="flex-1 mx-auto w-full max-w-6xl px-5 py-12 grid lg:grid-cols-[1fr_0.85fr] gap-10">
        {/* form */}
        <div>
          <p className="kicker text-smoke">Step 1 of 1 · Join GymFlow</p>
          <h1 className="display text-4xl md:text-5xl mt-3">
            Set up your membership
          </h1>
          <p className="mt-3 text-smoke max-w-md">
            Your card is tokenised on this device. GymFlow and Somba store a
            token and the last four digits — never the full number.
          </p>

          <form onSubmit={submit} className="mt-8 space-y-5 max-w-lg">
            <div className="grid sm:grid-cols-2 gap-4">
              <Field label="Full name">
                <input
                  className={inputCls}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Adaeze Okafor"
                  autoComplete="name"
                />
              </Field>
              <Field label="Email">
                <input
                  className={inputCls}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@email.com"
                  type="email"
                  autoComplete="email"
                />
              </Field>
            </div>

            <div className="rounded-xl border border-concrete-2 bg-paper p-5">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold uppercase tracking-wide text-smoke">
                  Card details
                </span>
                <span className="kicker text-volt-deep flex items-center gap-1.5">
                  <LockIcon /> Tokenised
                </span>
              </div>
              <Field label="Card number">
                <input
                  className={`${inputCls} mono`}
                  value={card}
                  onChange={(e) => onCardChange(e.target.value)}
                  placeholder="4242 4242 4242 4242"
                  inputMode="numeric"
                />
              </Field>
              <div className="grid grid-cols-2 gap-4 mt-4">
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
            </div>

            {error && (
              <p className="text-sm text-danger font-medium" role="alert">
                {error}
              </p>
            )}

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              disabled={busy}
            >
              {busy
                ? "Tokenising card…"
                : plan.trial_days > 0
                  ? `Start ${plan.trial_days}-day free trial`
                  : `Join & pay ${naira(plan.amount)}`}
            </Button>
            <p className="text-xs text-smoke-2 text-center">
              This is a demo. No real card is charged and no money moves.
            </p>
          </form>
        </div>

        {/* summary */}
        <aside className="lg:sticky lg:top-12 self-start">
          <div className="rounded-2xl bg-ink text-paper p-6">
            <p className="kicker text-paper/50">Your pass preview</p>
            <div className="mt-4 flex justify-center">
              <MembershipCard
                customer={{
                  name: name.trim() || "Your name",
                  card_last4: digits.slice(-4) || "0000",
                }}
                plan={plan}
                status={plan.trial_days > 0 ? "trialing" : "active"}
                memberId="SUB_PREVIEW"
              />
            </div>

            <div className="mt-6 border-t border-ink-3 pt-5">
              <div className="flex items-center justify-between">
                <span className="text-sm text-paper/60">Plan</span>
                <div className="flex gap-1.5">
                  {PLANS.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => selectPlan(p.id)}
                      className={`px-2.5 py-1 rounded-full text-xs font-semibold transition-colors ${
                        p.id === planId
                          ? "bg-volt text-ink"
                          : "bg-ink-2 text-paper/60 hover:text-paper"
                      }`}
                    >
                      {p.name}
                    </button>
                  ))}
                </div>
              </div>
              <div className="mt-4 flex items-end justify-between">
                <span className="text-sm text-paper/60">
                  {plan.trial_days > 0 ? "Due today" : "Due now"}
                </span>
                <span className="display text-3xl text-volt">
                  {plan.trial_days > 0 ? "₦0" : naira(plan.amount)}
                </span>
              </div>
              <p className="mt-2 text-xs text-paper/50">
                {plan.trial_days > 0
                  ? `Then ${naira(plan.amount)}/month after your trial. First bill on day ${plan.trial_days}.`
                  : `${naira(plan.amount)} billed monthly. Switch or cancel anytime.`}
              </p>
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
}

function LockIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden>
      <rect x="4" y="10" width="16" height="11" rx="2" fill="currentColor" />
      <path
        d="M8 10V7a4 4 0 0 1 8 0v3"
        stroke="currentColor"
        strokeWidth="2.2"
        fill="none"
      />
    </svg>
  );
}
