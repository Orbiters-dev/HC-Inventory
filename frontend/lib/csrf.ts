/**
 * Django CSRF 토큰 / 일반 cookie 추출.
 *
 * ONZ APP 의 utils.js getCSRFToken + helpers/csrf.js getCookie 의 dashboard 포팅.
 * url_swap plan v9 Phase 1 — 계산/서류/재고 모듈 흡수.
 */
export function getCSRFToken(): string {
  return getCookie("csrftoken") || "";
}

export function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  if (!document.cookie || document.cookie === "") return null;
  const cookies = document.cookie.split(";");
  for (const c of cookies) {
    const cookie = c.trim();
    if (cookie.substring(0, name.length + 1) === name + "=") {
      return decodeURIComponent(cookie.substring(name.length + 1));
    }
  }
  return null;
}
