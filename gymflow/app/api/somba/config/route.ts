import { isLive } from "@/lib/server/somba";

export async function GET() {
  return Response.json({ live: isLive(), base: "https://somba.ddns.net" });
}
