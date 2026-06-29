import { STATE_META } from "@/lib/states";
import type { Customer, Plan, SubscriptionStatus } from "@/lib/types";

// Signature element: a physical-feeling membership card that reflects state.
export function MembershipCard({
  customer,
  plan,
  status,
  memberId,
}: {
  customer: { name: string; card_last4?: string };
  plan: Pick<Plan, "name"> | undefined;
  status: SubscriptionStatus;
  memberId: string;
}) {
  const m = STATE_META[status];
  const inRecovery = status === "past_due" || status === "payment_uncertain";

  return (
    <div className="relative w-full max-w-[420px] aspect-[1.586/1] select-none">
      {/* the card */}
      <div className="foil absolute inset-0 rounded-2xl border border-ink-3 shadow-[0_30px_60px_-20px_rgba(0,0,0,0.6)] overflow-hidden">
        {/* faint embossed pattern */}
        <div
          className="absolute inset-0 opacity-[0.06]"
          style={{
            backgroundImage:
              "repeating-linear-gradient(135deg, #fff 0 1px, transparent 1px 9px)",
          }}
        />
        {/* recovery hazard edge */}
        {inRecovery && (
          <div className="hazard-thin absolute left-0 top-0 h-full w-1.5" />
        )}

        <div className="relative h-full p-6 flex flex-col justify-between text-paper">
          <div className="flex items-start justify-between">
            <div>
              <div className="display text-volt text-2xl leading-none">
                GymFlow
              </div>
              <div className="kicker text-smoke-2 mt-1">Member Pass</div>
            </div>
            <span
              className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide ${
                m.tone === "good"
                  ? "border-volt/50 text-volt"
                  : m.tone === "warn"
                    ? "border-due/60 text-due"
                    : m.tone === "frozen"
                      ? "border-frozen/60 text-frozen"
                      : "border-smoke text-smoke-2"
              }`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${m.dot}`} />
              {m.label}
            </span>
          </div>

          {/* chip */}
          <div className="flex items-center gap-3">
            <div className="h-7 w-10 rounded-md bg-gradient-to-br from-volt to-volt-deep opacity-90" />
            <div className="mono text-xs tracking-[0.3em] text-smoke-2">
              •••• •••• •••• {customer.card_last4 ?? "0000"}
            </div>
          </div>

          <div className="flex items-end justify-between">
            <div>
              <div className="kicker text-smoke-2">Member</div>
              <div className="font-semibold text-lg leading-tight">
                {customer.name}
              </div>
              <div className="mono text-[11px] text-smoke-2 mt-0.5">
                {memberId}
              </div>
            </div>
            <div className="text-right">
              <div className="kicker text-smoke-2">Plan</div>
              <div className="display text-xl text-paper">
                {plan?.name ?? "—"}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
