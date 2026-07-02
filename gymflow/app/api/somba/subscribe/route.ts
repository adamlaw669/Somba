import { somba } from "@/lib/server/somba";
import { ensurePlan, type Tier } from "@/lib/server/catalog";
import { errorResponse } from "@/lib/server/respond";

interface Body {
  name: string;
  email: string;
  tier: Tier;
}

export async function POST(request: Request) {
  try {
    const { name, email, tier } = (await request.json()) as Body;
    if (!name || !email || !tier) {
      return Response.json(
        { error: { code: "invalid_request", message: "name, email and tier are required" } },
        { status: 400 },
      );
    }
    const plan = await ensurePlan(tier);
    const { customer } = await somba<{ customer: Record<string, unknown> }>(
      "/v1/customers",
      { method: "POST", body: { name, email } },
    );
    const { subscription } = await somba<{
      subscription: Record<string, unknown>;
    }>("/v1/subscriptions", {
      method: "POST",
      body: { plan_id: plan.id, customer_id: (customer as { id: number }).id },
    });
    return Response.json({ subscription, customer, tier, plan });
  } catch (e) {
    return errorResponse(e);
  }
}
