import { BASE_PATH } from "@/lib/constants";

export interface Session {
  authenticated: boolean;
  user?: string;
  password_change_required?: boolean;
}

/** GET /auth/session/status/ — csrftoken 쿠키도 함께 내려옴(getCSRFToken 읽기용). */
export async function fetchSession(): Promise<Session> {
  try {
    const res = await fetch(`${BASE_PATH}/auth/session/status/`, {
      credentials: "include",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return { authenticated: false };
    return (await res.json()) as Session;
  } catch {
    return { authenticated: false };
  }
}
