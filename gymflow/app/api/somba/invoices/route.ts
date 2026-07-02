import { somba } from "@/lib/server/somba";
import { errorResponse } from "@/lib/server/respond";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const subId = url.searchParams.get("subscription_id");
    const q = subId ? `?subscription_id=${encodeURIComponent(subId)}` : "";
    const data = await somba<{ invoices: unknown[] }>(`/v1/invoices${q}`);
    return Response.json(data);
  } catch (e) {
    return errorResponse(e);
  }
}
