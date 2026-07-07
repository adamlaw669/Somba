import { somba } from "./somba";

// Our three presentation tiers, mapped to real Somba plans by name.
export type Tier = "basic" | "standard" | "premium";

const TIER_DEFAULTS: Record<
  Tier,
  { name: string; amount: number; trial_days: number }
> = {
  basic: { name: "Basic", amount: 500000, trial_days: 7 },
  standard: { name: "Standard", amount: 900000, trial_days: 7 },
  premium: { name: "Premium", amount: 1500000, trial_days: 0 },
};

export interface ApiPlan {
  id: number;
  name: string;
  amount: number;
  currency: string;
  interval: string;
  interval_count: number;
  trial_days: number;
  status: string;
}

export function tierForName(name: string): Tier | null {
  const n = name.trim().toLowerCase();
  if (n === "basic" || n === "standard" || n === "premium") return n as Tier;
  return null;
}

export async function listPlans(): Promise<ApiPlan[]> {
  const { plans } = await somba<{ plans: ApiPlan[] }>("/v1/plans");
  return plans ?? [];
}

/** Returns the real plan for a tier, creating it if the merchant doesn't have it yet. */
export async function ensurePlan(tier: Tier): Promise<ApiPlan> {
  const plans = await listPlans();
  const existing = plans.find(
    (p) => tierForName(p.name) === tier && p.status === "active",
  );
  if (existing) return existing;

  const d = TIER_DEFAULTS[tier];
  const { plan } = await somba<{ plan: ApiPlan }>("/v1/plans", {
    method: "POST",
    body: {
      name: d.name,
      amount: d.amount,
      interval: "month",
      trial_days: d.trial_days,
    },
  });
  return plan;
}

/** All three tiers, ensuring each exists. */
export async function ensureCatalog(): Promise<Record<Tier, ApiPlan>> {
  const [basic, standard, premium] = await Promise.all([
    ensurePlan("basic"),
    ensurePlan("standard"),
    ensurePlan("premium"),
  ]);
  return { basic, standard, premium };
}
