import { somba } from "@/lib/server/somba";
import { ensurePlan, type Tier } from "@/lib/server/catalog";
import { errorResponse } from "@/lib/server/respond";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const id = url.searchParams.get("id");
    const customerId = url.searchParams.get("customer_id");
    if (!id) {
      return Response.json(
        { error: { code: "invalid_request", message: "id is required" } },
        { status: 400 },
      );
    }
    const { subscription } = await somba<{ subscription: unknown }>(
      `/v1/subscriptions/${id}`,
    );
    let customer: unknown = null;
    if (customerId) {
      const c = await somba<{ customer: unknown }>(
        `/v1/customers/${customerId}`,
      );
      customer = c.customer;
    }
    return Response.json({ subscription, customer });
  } catch (e) {
    return errorResponse(e);
  }
}

export async function PATCH(request: Request) {
  try {
    const { id, tier } = (await request.json()) as { id: number; tier: Tier };
    if (!id || !tier) {
      return Response.json(
        { error: { code: "invalid_request", message: "id and tier are required" } },
        { status: 400 },
      );
    }
    const plan = await ensurePlan(tier);
    const result = await somba<{ subscription: unknown; proration: unknown }>(
      `/v1/subscriptions/${id}`,
      { method: "PATCH", body: { plan_id: plan.id } },
    );
    return Response.json({ ...result, tier, plan });
  } catch (e) {
    return errorResponse(e);
  }
}
