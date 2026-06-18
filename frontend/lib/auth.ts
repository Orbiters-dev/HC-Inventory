import { BASE_PATH } from "@/lib/constants";
import { getCSRFToken } from "@/lib/csrf";

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

/**
 * POST /auth/logout/ — 서버 세션 파기.
 * fetch 만 담당하고 페이지 이동(router.replace)은 호출측이 try/finally 로 보장한다
 * (네트워크/CSRF 실패해도 로그인 화면으로 이동 = best-effort).
 */
export async function signOut(): Promise<void> {
  await fetch(`${BASE_PATH}/auth/logout/`, {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRFToken": getCSRFToken() },
  });
}
