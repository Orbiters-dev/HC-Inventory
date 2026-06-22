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
  // 서버→자기 공개도메인(https) 호출은 헤어핀 NAT 로 실패할 수 있어, 같은 호스트의
  // Django(내부 8010) 를 직접 호출한다. (nginx 가 /auth/ → 127.0.0.1:8010 으로 프록시)
  const candidates = [
    "http://127.0.0.1:8010/auth/session/status/",
    new URL("/auth/session/status/", request.url).toString(),
  ];
  for (const url of candidates) {
    try {
      const res = await fetch(url, {
        headers: {
          cookie: request.headers.get("cookie") ?? "",
          accept: "application/json",
          host: request.nextUrl.host,
        },
      });
      if (res.ok) {
        const data = await res.json();
        if (data?.authenticated) {
          return NextResponse.next();
        }
        // 인증 응답은 받았으나 미인증 → 로그인으로
        return NextResponse.redirect(new URL("/login", request.url));
      }
    } catch {
      // 이 후보 실패 → 다음 후보 시도
    }
  }
  return NextResponse.redirect(new URL("/login", request.url));
}

export const config = {
  matcher: ["/inventory", "/inventory-report.html"],
};
