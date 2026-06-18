"use client";

// 경량 좌측 사이드바 셸 — tools.orbiters.co.kr 멀티모듈 허브 레이아웃.
// 단일 외부계정 운영(권한 시스템 없음)이라 대시보드 app-sidebar 의 RBAC/탭카탈로그/
// i18n/theme-toggle 군더더기를 걷어낸 신규 경량 버전.
// 데스크톱: 고정 좌측 사이드바. 모바일(<md): 햄버거 드로어.

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Boxes,
  Calculator,
  ClipboardList,
  LogOut,
  Menu,
  User,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { signOut } from "@/lib/auth";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

// 향후 하위 모듈(/서류, /재고 등)은 여기 그룹/항목 추가만으로 확장.
const NAV_GROUPS: NavGroup[] = [
  {
    label: "도구",
    items: [
      { href: "/calculator", label: "수출 비용 계산기", icon: Calculator },
      { href: "/history", label: "계산 이력", icon: ClipboardList },
    ],
  },
  {
    label: "계정",
    items: [{ href: "/mypage", label: "프로필", icon: User }],
  },
];

function isActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(href + "/");
}

/** 사이드바 본문 — 데스크톱 고정 패널 + 모바일 드로어가 공유. */
function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname() || "/";
  const router = useRouter();

  async function handleLogout() {
    onNavigate?.();
    // signOut 은 fetch 만 담당 — 이동은 호출측 finally 가 보장(실패해도 로그인 화면으로).
    try {
      await signOut();
    } finally {
      router.replace("/login");
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* 브랜드 */}
      <div className="border-sidebar-border flex items-center gap-2.5 border-b px-5 py-4">
        <span className="bg-sidebar-primary text-sidebar-primary-foreground flex size-8 items-center justify-center rounded-lg">
          <Boxes className="size-4" />
        </span>
        <div className="leading-tight">
          <div className="text-sidebar-foreground text-sm font-semibold">
            HC Tools
          </div>
          <div className="text-muted-foreground text-[11px]">수출 도구</div>
        </div>
      </div>

      {/* 메뉴 */}
      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
        {NAV_GROUPS.map((group) => (
          <div key={group.label}>
            <div className="text-muted-foreground px-2 pb-1.5 text-[11px] font-medium tracking-wide uppercase">
              {group.label}
            </div>
            <ul className="space-y-0.5">
              {group.items.map((item) => {
                const Icon = item.icon;
                const active = isActive(pathname, item.href);
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={onNavigate}
                      aria-current={active ? "page" : undefined}
                      className={cn(
                        "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors",
                        active
                          ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                          : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
                      )}
                    >
                      <Icon className="size-4 shrink-0" />
                      <span className="truncate">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* 로그아웃 */}
      <div className="border-sidebar-border border-t p-3">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={handleLogout}
          className="text-muted-foreground hover:text-sidebar-accent-foreground w-full justify-start gap-2.5 px-2.5"
        >
          <LogOut className="size-4" />
          <span>로그아웃</span>
        </Button>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  // 라우트 변경 시 모바일 드로어 자동 닫기(메뉴 열린 채 다음 페이지 렌더 차단).
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  // Esc 로 드로어 닫기(a11y).
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <div className="bg-background flex min-h-screen">
      {/* 데스크톱 고정 사이드바 */}
      <aside className="bg-sidebar border-sidebar-border hidden w-60 shrink-0 border-r md:block">
        <div className="sticky top-0 h-screen">
          <SidebarNav />
        </div>
      </aside>

      {/* 모바일 드로어 */}
      {open && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
          <aside
            className="bg-sidebar border-sidebar-border absolute inset-y-0 left-0 w-64 border-r shadow-xl"
            role="dialog"
            aria-modal="true"
            aria-label="메뉴"
          >
            <SidebarNav onNavigate={() => setOpen(false)} />
          </aside>
        </div>
      )}

      {/* 콘텐츠 영역 */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* 모바일 상단바 */}
        <header className="bg-background sticky top-0 z-30 flex items-center gap-2 border-b px-4 py-2.5 md:hidden">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            onClick={() => setOpen(true)}
            aria-label="메뉴 열기"
          >
            <Menu className="size-5" />
          </Button>
          <span className="text-sm font-semibold">HC Tools</span>
        </header>
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
