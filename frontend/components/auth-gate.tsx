"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { fetchSession, type Session } from "@/lib/auth";

const PUBLIC_PATHS = ["/login"];

/**
 * 단일계정 인증 게이트.
 * - 미로그인 → /login
 * - password_change_required → /mypage (첫 로그인 강제변경)
 * - /login 은 게이트 미적용(로그인 대상)
 */
export function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [session, setSession] = useState<Session | null>(null);
  const isPublic = PUBLIC_PATHS.includes(pathname);

  useEffect(() => {
    let active = true;
    fetchSession().then((s) => {
      if (!active) return;
      setSession(s);
      if (isPublic) return;
      if (!s.authenticated) {
        router.replace("/login");
      } else if (s.password_change_required && pathname !== "/mypage") {
        router.replace("/mypage");
      }
    });
    return () => {
      active = false;
    };
  }, [pathname, router, isPublic]);

  if (isPublic) return <>{children}</>;
  if (session === null) {
    return <div className="text-muted-foreground p-6 text-sm">로딩 중…</div>;
  }
  if (!session.authenticated) {
    return <div className="text-muted-foreground p-6 text-sm">로그인으로 이동 중…</div>;
  }
  if (session.password_change_required && pathname !== "/mypage") {
    return (
      <div className="text-muted-foreground p-6 text-sm">
        비밀번호 변경으로 이동 중…
      </div>
    );
  }
  // 인증 완료 + 비번변경 불요 = 정상 진입 → 사이드바 셸로 감싼다.
  // (위 분기들: /login·로딩(null)·미인증·강제변경 상태는 셸 미마운트)
  return <AppShell>{children}</AppShell>;
}
