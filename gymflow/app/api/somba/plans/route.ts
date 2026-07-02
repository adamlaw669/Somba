import { ensureCatalog } from "@/lib/server/catalog";
import { errorResponse } from "@/lib/server/respond";

export async function GET() {
  try {
    const cat = await ensureCatalog();
    const plans = (["basic", "standard", "premium"] as const).map((tier) => ({
      tier,
      ...cat[tier],
    }));
    return Response.json({ plans });
  } catch (e) {
    return errorResponse(e);
  }
}
