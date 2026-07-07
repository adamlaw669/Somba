import { somba } from "@/lib/server/somba";
import { errorResponse } from "@/lib/server/respond";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const params = new URLSearchParams();
    const type = url.searchParams.get("event_type");
    const status = url.searchParams.get("status");
    if (type) params.set("event_type", type);
    if (status) params.set("status", status);
    const q = params.toString() ? `?${params}` : "";
    const data = await somba<{ events: unknown[] }>(`/v1/events${q}`);
    return Response.json(data);
  } catch (e) {
    return errorResponse(e);
  }
}
