// ── Centralized API client for the Foodly frontend ──────────
// All API calls go through this module instead of hardcoding localhost:8000

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

// NEXT_PUBLIC_ADMIN_SECRET removed — admin auth is now role-based JWT.
// See authHeaders() below; admin routes require a logged-in user whose
// account has role="admin" (checked server-side).

/** Build a full API URL from a path like "/api/v1/meals" */
export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

/** Standard headers for user-authenticated (and admin) requests */
export function authHeaders(): Record<string, string> {
  const token =
    typeof window !== "undefined"
      ? window.localStorage.getItem("authToken")
      : null;
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

/** Confidence score color utility */
export const CONFIDENCE_COLOR = (c: number) =>
  c >= 80
    ? "text-emerald-600 bg-emerald-50"
    : c >= 50
    ? "text-amber-600 bg-amber-50"
    : "text-rose-600 bg-rose-50";