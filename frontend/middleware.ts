import { NextRequest, NextResponse } from "next/server";

/**
 * /inventory (및 /inventory-report.html) 로그인 게이트.
 *
 * 재고 리포트는 정적 HTML(public) 이라 계산기 앱의 AuthGate(React) 를 거치지 않는다.
 * 그래서 여기서 계산기와 "동일한 단일 HC 세션" 을 확인해 미인증이면 /login 으로 보낸다.
 * (인증 통과 시 next() → next.config 의 rewrite 가 /inventory→리포트를 서빙)
 *
 * fail-closed: 세션 확인이 실패하면 안전하게 /login 으로 (데이터 노출 방지).
 */
export async function middleware(request: NextRequest) {
  try {
    const statusUrl = new URL("/auth/session/status/", request.url);
    const res = await fetch(statusUrl, {
      headers: {
        cookie: request.headers.get("cookie") ?? "",
        accept: "application/json",
      },
    });
    if (res.ok) {
      const data = await res.json();
      if (data?.authenticated) {
        return NextResponse.next();
      }
    }
  } catch {
    // 세션 확인 실패 → 로그인으로 (fail-closed)
  }
  return NextResponse.redirect(new URL("/login", request.url));
}

export const config = {
  matcher: ["/inventory", "/inventory-report.html"],
};
