export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const WS_URL = API_URL.replace(/^https/, "wss").replace(/^http/, "ws");

/** Builds a signed, user-scoped download URL for a workspace file and opens
 * it in a new tab, triggering the browser's native download. Fetches a
 * short-lived backend auth token first (window.open can't set headers, so
 * the token travels as a query param — same trade-off as any presigned
 * download link). */
export async function downloadWorkspaceFile(filename: string, userId: string) {
  const tokenRes = await fetch("/api/backend-token");
  if (!tokenRes.ok) {
    throw new Error("Could not authorize download — try signing in again.");
  }
  const { token } = await tokenRes.json();

  const url = `${API_URL}/workspace/download/${filename}?user_id=${encodeURIComponent(userId)}&token=${encodeURIComponent(token)}`;
  window.open(url, "_blank");
}
