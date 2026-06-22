import { NextRequest, NextResponse } from "next/server";

/**
 * /inventory (및 /inventory-report.html) 로그인 게이트.
 *
 * 재고 리포트는 정적 HTML(public) 이라 계산기 앱의 AuthGate(React) 를 거치지 않는다.
 * 그래서 여기서 "계산기 로그인 시 발급되는 Django 세션 쿠키(sessionid) 존재" 를
 * 확인해 미인증이면 /login 으로 보낸다. (로그인하면 sessionid 쿠키가 생김)
 *
 * 주: 미들웨어에서 세션 "값" 검증(Django 호출)은 self-host 런타임/헤어핀 문제로
 * 불안정하므로, 쿠키 존재로 게이트한다. (랜덤/크롤러 차단 목적의 기본 게이트.
 * 더 강한 보호가 필요하면 nginx 단 인증으로 보강.)
 */
export function middleware(request: NextRequest) {
  if (request.cookies.has("sessionid")) {
    return NextResponse.next();
  }
  return NextResponse.redirect(new URL("/login", request.url));
}

export const config = {
  matcher: ["/inventory", "/inventory-report.html"],
};
