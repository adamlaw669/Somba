import { SombaError } from "./somba";

// Turns a thrown error into a consistent JSON error response for our proxy.
export function errorResponse(e: unknown): Response {
  if (e instanceof SombaError) {
    return Response.json(
      { error: { code: e.code, message: e.message } },
      { status: e.status },
    );
  }
  const message = e instanceof Error ? e.message : "Unexpected error";
  return Response.json(
    { error: { code: "proxy_error", message } },
    { status: 502 },
  );
}
