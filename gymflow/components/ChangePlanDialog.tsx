"use client";

import { useState } from "react";
import { PLANS, planById } from "@/lib/plans";
import { naira, prorate } from "@/lib/money";
import { useDemo } from "@/lib/store";
import { Button } from "./ui";

export function ChangePlanDialog({ onClose }: { onClose: () => void }) {
  const subscription = useDemo((s) => s.subscription)!;
  const changePlan = useDemo((s) => s.changePlan);
  const current = planById(subscription.plan_id)!;
  const [target, setTarget] = useState(
    PLANS.find((p) => p.id !== current.id)!.id,
  );

  const newPlan = planById(target)!;
  const daysInPeriod = 30;
  const msLeft =
    new Date(subscription.current_period_end).getTime() - Date.now();
  const daysRemaining = Math.max(
    0,
    Math.min(daysInPeriod, Math.round(msLeft / 86_400_000)),
  );
  const { credit, charge, net } = prorate(
    current.amount,
    newPlan.amount,
    daysInPeriod,
    daysRemaining,
  );

  const confirm = () => {
    changePlan(target);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-ink/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md bg-paper rounded-2xl border border-concrete-2 p-6 fade-up"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <p className="kicker text-smoke">Change plan · prorated to the day</p>
        <h2 className="display text-3xl mt-2">Switch your tier</h2>

        <div className="mt-5 grid grid-cols-3 gap-2">
          {PLANS.map((p) => {
            const isCurrent = p.id === current.id;
            const isTarget = p.id === target;
            return (
              <button
                key={p.id}
                disabled={isCurrent}
                onClick={() => setTarget(p.id)}
                className={`rounded-xl border p-3 text-left transition-colors ${
                  isCurrent
                    ? "border-concrete-2 bg-concrete opacity-50 cursor-not-allowed"
                    : isTarget
                      ? "border-ink bg-ink text-paper"
                      : "border-concrete-2 hover:border-ink"
                }`}
              >
                <div className="font-semibold">{p.name}</div>
                <div
                  className={`text-xs mt-0.5 ${isTarget && !isCurrent ? "text-paper/60" : "text-smoke"}`}
                >
                  {naira(p.amount)}
                </div>
                {isCurrent && (
                  <div className="mono text-[10px] text-smoke-2 mt-1">current</div>
                )}
              </button>
            );
          })}
        </div>

        <div className="mt-5 rounded-xl bg-concrete border border-concrete-2 p-4 space-y-2 text-sm">
          <Row
            label={`Credit for ${daysRemaining} unused days on ${current.name}`}
            value={`−${naira(credit)}`}
          />
          <Row
            label={`${newPlan.name} for ${daysRemaining} remaining days`}
            value={naira(charge)}
          />
          <div className="border-t border-concrete-2 pt-2 flex items-center justify-between">
            <span className="font-semibold">
              {net >= 0 ? "Charged today" : "Credited to your account"}
            </span>
            <span className="display text-2xl">
              {naira(Math.abs(net))}
            </span>
          </div>
        </div>
        <p className="mt-2 text-xs text-smoke-2">
          {net >= 0
            ? "Only the difference moves. Your billing date stays the same."
            : "A downgrade — the credit is banked against your next renewal."}
        </p>

        <div className="mt-6 flex gap-3">
          <Button variant="ghost" onClick={onClose} className="flex-1">
            Cancel
          </Button>
          <Button variant="primary" onClick={confirm} className="flex-1">
            Switch to {newPlan.name}
          </Button>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-smoke">{label}</span>
      <span className="mono">{value}</span>
    </div>
  );
}
