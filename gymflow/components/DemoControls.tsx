"use client";

import { useRouter } from "next/navigation";
import { useDemo } from "@/lib/store";
import type { SubscriptionStatus } from "@/lib/types";

// The demo cockpit: trigger every interesting billing scenario and watch the
// membership react. Clearly marked as simulation so it's never mistaken for UI.
export function DemoControls({ status }: { status: SubscriptionStatus }) {
  const router = useRouter();
  const d = useDemo();

  const Btn = ({
    onClick,
    children,
    tone = "default",
  }: {
    onClick: () => void;
    children: React.ReactNode;
    tone?: "default" | "good" | "warn" | "danger";
  }) => (
    <button
      onClick={onClick}
      className={`text-left rounded-lg border px-3.5 py-3 text-sm font-medium transition-colors ${
        tone === "good"
          ? "border-volt-deep/40 hover:bg-volt hover:text-ink hover:border-ink"
          : tone === "warn"
            ? "border-due/40 text-due hover:bg-due hover:text-paper hover:border-due"
            : tone === "danger"
              ? "border-danger/40 text-danger hover:bg-danger hover:text-paper hover:border-danger"
              : "border-ink-3 text-paper/80 hover:bg-paper/10 hover:text-paper"
      }`}
    >
      {children}
    </button>
  );

  return (
    <section className="rounded-2xl bg-ink text-paper p-6 border-2 border-dashed border-ink-3">
      <div className="flex items-center justify-between gap-3 mb-1">
        <p className="kicker text-volt flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-volt live-dot" />
          Demo cockpit
        </p>
        <button
          onClick={() => {
            d.reset();
            router.push("/");
          }}
          className="text-xs font-semibold text-paper/50 hover:text-paper underline-offset-2 hover:underline"
        >
          Reset demo
        </button>
      </div>
      <p className="text-sm text-paper/60 mb-5 max-w-xl">
        Drive the membership through Somba&apos;s lifecycle. Each action fires real
        webhook events into the{" "}
        <a href="/events" className="text-volt underline-offset-2 hover:underline">
          event viewer
        </a>
        .
      </p>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
        {status === "trialing" && (
          <Btn tone="good" onClick={d.activateFromTrial}>
            ▸ Convert trial → first charge
          </Btn>
        )}

        {(status === "active" || status === "trialing") && (
          <>
            <Btn tone="good" onClick={d.renew}>
              ▸ Renew now (charge succeeds)
            </Btn>
            <Btn tone="warn" onClick={() => d.triggerFailure("empty_account")}>
              ▸ Renewal fails: empty account
            </Btn>
            <Btn tone="warn" onClick={() => d.triggerFailure("broken_card")}>
              ▸ Hard decline → transfer fallback
            </Btn>
            <Btn onClick={d.triggerTimeout}>▸ Charge times out → verifying</Btn>
            <Btn tone="danger" onClick={() => d.triggerFailure("risk")}>
              ▸ Risk block (stop &amp; notify)
            </Btn>
          </>
        )}

        {status === "past_due" && (
          <>
            <Btn tone="good" onClick={d.retryPayment}>
              ▸ Retry charge now (heals)
            </Btn>
            {d.transfer && (
              <Btn tone="good" onClick={d.simulateTransferPush}>
                ▸ Simulate transfer received
              </Btn>
            )}
          </>
        )}

        {status === "payment_uncertain" && (
          <>
            <Btn tone="good" onClick={() => d.resolveUncertain(true)}>
              ▸ Verify pass: it succeeded
            </Btn>
            <Btn tone="warn" onClick={() => d.resolveUncertain(false)}>
              ▸ Verify pass: it failed
            </Btn>
          </>
        )}

        {status === "paused" && (
          <Btn tone="good" onClick={d.resume}>
            ▸ Resume membership
          </Btn>
        )}

        {(status === "cancelled" || status === "expired") && (
          <Btn tone="good" onClick={() => router.push("/")}>
            ▸ Start a new membership
          </Btn>
        )}
      </div>
    </section>
  );
}
