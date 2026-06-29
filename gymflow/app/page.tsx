"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { PLANS } from "@/lib/plans";
import { naira } from "@/lib/money";
import { useDemo, useHydrated } from "@/lib/store";
import { Button, ButtonLink } from "@/components/ui";
import { SiteFooter } from "@/components/AppShell";

export default function Landing() {
  const router = useRouter();
  const hydrated = useHydrated();
  const selectPlan = useDemo((s) => s.selectPlan);
  const subscription = useDemo((s) => s.subscription);
  const customer = useDemo((s) => s.customer);

  const choose = (planId: string) => {
    selectPlan(planId);
    router.push("/join");
  };

  const hasMembership = hydrated && subscription && customer;

  return (
    <div className="min-h-screen flex flex-col">
      {/* marketing header */}
      <header className="absolute top-0 inset-x-0 z-30">
        <div className="mx-auto max-w-6xl px-5 h-16 flex items-center justify-between">
          <span className="display text-paper text-2xl leading-none">
            Gym<span className="text-volt">Flow</span>
          </span>
          <div className="flex items-center gap-3">
            <a
              href="#plans"
              className="hidden sm:inline text-sm font-semibold text-paper/70 hover:text-paper transition-colors"
            >
              Plans
            </a>
            {hasMembership ? (
              <ButtonLink href="/membership" variant="primary">
                My membership
              </ButtonLink>
            ) : (
              <a
                href="#plans"
                className="text-sm font-semibold text-volt hover:text-paper transition-colors"
              >
                Join →
              </a>
            )}
          </div>
        </div>
      </header>

      {/* ---------- HERO ---------- */}
      <section className="relative bg-ink text-paper overflow-hidden">
        <div className="relative">
          {/* athlete backdrop, weighted right; dark gradient keeps the left legible */}
          <Image
            src="/img/hero.png"
            alt=""
            fill
            priority
            sizes="100vw"
            className="object-cover object-right opacity-80"
          />
          <div className="absolute inset-0 bg-[linear-gradient(90deg,#0a0a0a_0%,#0a0a0a_38%,rgba(10,10,10,0.55)_70%,rgba(10,10,10,0.2)_100%)]" />
          <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-b from-transparent to-ink" />
          <div className="pointer-events-none absolute -top-40 -right-32 h-[36rem] w-[36rem] rounded-full bg-volt/20 blur-[120px]" />
        <div className="relative z-10 mx-auto max-w-6xl px-5 pt-32 pb-20 md:pt-44 md:pb-32">
          <div className="fade-up max-w-2xl">
            <p className="kicker text-volt">Lagos · Strength &amp; Conditioning</p>
            <h1 className="display text-6xl sm:text-7xl md:text-8xl mt-5">
              Train hard.
              <br />
              <span className="text-volt">Billing</span>, handled.
            </h1>
            <p className="mt-6 text-lg text-paper/70 max-w-md">
              GymFlow memberships run themselves. When a payment slips, we
              don&apos;t cut you off — we recover it quietly and heal your pass
              back to active. You just keep training.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <a href="#plans">
                <Button variant="primary">Choose your plan</Button>
              </a>
              <ButtonLink
                href={hasMembership ? "/membership" : "/join"}
                variant="outline"
                className="!border-paper/30 !text-paper hover:!bg-paper hover:!text-ink"
              >
                {hasMembership ? "Open my pass" : "See the demo flow"}
              </ButtonLink>
            </div>
            <dl className="mt-12 grid grid-cols-3 gap-6 max-w-md">
              {[
                ["7 states", "Every billing outcome"],
                ["0", "Members lost to silent fails"],
                ["100%", "Naira accounted for"],
              ].map(([n, l]) => (
                <div key={l}>
                  <dt className="display text-3xl text-volt">{n}</dt>
                  <dd className="text-xs text-paper/60 mt-1 leading-snug">{l}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
        </div>

        {/* hazard tape divider + lifecycle ticker */}
        <div className="hazard-thin h-3" />
        <div className="bg-ink-2 border-y border-ink-3 overflow-hidden">
          <div className="flex whitespace-nowrap py-3 ticker-track">
            {[0, 1].map((dup) => (
              <div key={dup} className="flex items-center" aria-hidden={dup === 1}>
                {[
                  "Sign up",
                  "Active",
                  "Payment fails",
                  "Recover by timing",
                  "Transfer fallback",
                  "Healed → Active",
                  "Every naira proven",
                ].map((t, i) => (
                  <span
                    key={`${dup}-${i}`}
                    className="mx-6 kicker text-paper/50 flex items-center gap-6"
                  >
                    {t}
                    <span className="text-volt">/</span>
                  </span>
                ))}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- PLANS ---------- */}
      <section id="plans" className="bg-concrete scroll-mt-16">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-10">
            <div>
              <p className="kicker text-smoke">Membership</p>
              <h2 className="display text-4xl md:text-5xl mt-3">Pick your tier</h2>
            </div>
            <p className="text-smoke max-w-sm">
              Billed monthly in naira. Cancel or switch any time — switches are
              prorated to the day.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-5">
            {PLANS.map((plan) => (
              <div
                key={plan.id}
                className={`relative flex flex-col rounded-2xl border overflow-hidden transition-transform hover:-translate-y-1 ${
                  plan.featured
                    ? "bg-ink text-paper border-ink shadow-[0_24px_50px_-24px_rgba(0,0,0,0.5)]"
                    : "bg-paper text-ink border-concrete-2"
                }`}
              >
                {plan.featured && (
                  <span className="absolute top-3 left-3 z-10 bg-volt text-ink text-[11px] font-bold uppercase tracking-wide px-3 py-1 rounded-full">
                    Most popular
                  </span>
                )}
                <div className="relative h-36">
                  <Image
                    src={`/img/tier-${plan.id.replace("plan_", "")}.png`}
                    alt={`${plan.name} training`}
                    fill
                    sizes="(max-width: 768px) 100vw, 33vw"
                    className="object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-ink/70 to-transparent" />
                </div>
                <div className="flex flex-col flex-1 p-7">
                <h3 className="display text-3xl">{plan.name}</h3>
                <p
                  className={`mt-1 text-sm ${plan.featured ? "text-paper/60" : "text-smoke"}`}
                >
                  {plan.tagline}
                </p>
                <div className="mt-6 flex items-baseline gap-1">
                  <span className="display text-4xl">{naira(plan.amount)}</span>
                  <span
                    className={`text-sm ${plan.featured ? "text-paper/60" : "text-smoke"}`}
                  >
                    /month
                  </span>
                </div>
                <p
                  className={`mt-2 text-xs font-semibold ${plan.featured ? "text-volt" : "text-volt-deep"}`}
                >
                  {plan.trial_days > 0
                    ? `${plan.trial_days}-day free trial`
                    : "Starts today"}
                </p>

                <ul className="mt-6 space-y-2.5 flex-1">
                  {plan.perks.map((perk) => (
                    <li key={perk} className="flex gap-2.5 text-sm">
                      <span
                        className={`mt-0.5 shrink-0 ${plan.featured ? "text-volt" : "text-volt-deep"}`}
                        aria-hidden
                      >
                        ▸
                      </span>
                      <span className={plan.featured ? "text-paper/85" : "text-ink/80"}>
                        {perk}
                      </span>
                    </li>
                  ))}
                </ul>

                <Button
                  variant={plan.featured ? "primary" : "dark"}
                  className="mt-7 w-full"
                  onClick={() => choose(plan.id)}
                >
                  Start {plan.name}
                </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- HOW RECOVERY WORKS ---------- */}
      <section className="bg-paper border-t border-concrete-2">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <p className="kicker text-smoke">Why your pass survives a bad day</p>
          <h2 className="display text-4xl md:text-5xl mt-3 max-w-2xl">
            Most failed payments aren&apos;t broken cards. They&apos;re empty
            accounts.
          </h2>
          <div className="grid md:grid-cols-3 gap-5 mt-10">
            {[
              {
                t: "Wait for payday",
                d: "If your account was empty this morning, that doesn't mean it'll be empty tonight. We retry when money is likely to be there — not in a noisy loop.",
              },
              {
                t: "Switch to transfer",
                d: "If the card is truly dead, we stop pulling. You get a dedicated account number to send a transfer to. Nigeria runs on transfers — so does recovery.",
              },
              {
                t: "Prove every naira",
                d: "Every charge is written down before it happens. If anything is uncertain, a verify pass settles the truth. No double charges, no silent losses.",
              },
            ].map((c, i) => (
              <div
                key={c.t}
                className="rounded-2xl border border-concrete-2 p-6 bg-concrete"
              >
                <span className="mono text-sm text-volt-deep">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <h3 className="display text-2xl mt-3">{c.t}</h3>
                <p className="mt-2 text-sm text-smoke leading-relaxed">{c.d}</p>
              </div>
            ))}
          </div>

          <div className="relative mt-12 rounded-2xl bg-ink text-paper overflow-hidden">
            <Image
              src="/img/atmosphere.png"
              alt=""
              fill
              sizes="100vw"
              className="object-cover opacity-40"
            />
            <div className="absolute inset-0 bg-[linear-gradient(90deg,#0a0a0a_30%,rgba(10,10,10,0.4)_100%)]" />
            <div className="relative z-10 p-8 md:p-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
              <div>
                <h3 className="display text-3xl">See it happen, live.</h3>
                <p className="mt-2 text-paper/70 max-w-lg">
                  Join, then break your own payment on purpose and watch the
                  membership recover itself — with every webhook event streaming
                  in real time.
                </p>
              </div>
              <a href="#plans" className="shrink-0">
                <Button variant="primary">Start the demo</Button>
              </a>
            </div>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
