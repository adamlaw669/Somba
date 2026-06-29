import type { Plan } from "./types";

// Real plan names, real naira amounts — seeded like the PRD's GymFlow demo.
export const PLANS: Plan[] = [
  {
    id: "plan_basic",
    name: "Basic",
    tagline: "Show up. Get it done.",
    amount: 500000, // ₦5,000
    currency: "NGN",
    interval: "month",
    trial_days: 7,
    perks: [
      "Full gym floor access",
      "2 group classes / week",
      "Locker + towel service",
      "Mobile check-in",
    ],
  },
  {
    id: "plan_standard",
    name: "Standard",
    tagline: "Train like you mean it.",
    amount: 900000, // ₦9,000
    currency: "NGN",
    interval: "month",
    trial_days: 7,
    featured: true,
    perks: [
      "Everything in Basic",
      "Unlimited group classes",
      "1 personal training session / month",
      "Sauna + recovery zone",
      "Guest pass / month",
    ],
  },
  {
    id: "plan_premium",
    name: "Premium",
    tagline: "The whole machine, no limits.",
    amount: 1500000, // ₦15,000
    currency: "NGN",
    interval: "month",
    trial_days: 0,
    perks: [
      "Everything in Standard",
      "Weekly 1:1 personal training",
      "Nutrition & InBody scans",
      "24/7 access, all branches",
      "Priority class booking",
    ],
  },
];

export function planById(id: string | null | undefined): Plan | undefined {
  return PLANS.find((p) => p.id === id);
}
