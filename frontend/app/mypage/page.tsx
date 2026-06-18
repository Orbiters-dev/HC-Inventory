"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { fetchSession, signOut } from "@/lib/auth";
import { BASE_PATH } from "@/lib/constants";
import { getCSRFToken } from "@/lib/csrf";

export default function MyPage() {
  const router = useRouter();
  const [account, setAccount] = useState("");
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSession().then((s) => setAccount(s.user ?? ""));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`${BASE_PATH}/auth/change-password/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({ current_password: current, new_password: next }),
      });
      const data = await res.json();
      if (!res.ok) {
        toast.error(data.error || "비밀번호 변경에 실패했습니다.");
        return;
      }
      toast.success("비밀번호가 변경되었습니다.");
      router.replace("/calculator");
    } catch {
      toast.error("네트워크 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  async function onLogout() {
    // signOut 은 fetch 만 — 이동은 finally 가 보장(실패해도 로그인 화면으로).
    try {
      await signOut();
    } finally {
      router.replace("/login");
    }
  }

  return (
    <div className="mx-auto max-w-md space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">프로필</h1>
        <p className="text-muted-foreground text-sm">
          계정 정보와 비밀번호를 관리합니다.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>계정 정보</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <dt className="text-muted-foreground">아이디</dt>
              <dd className="font-medium">{account || "—"}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>비밀번호 변경</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <Input
              type="password"
              placeholder="현재 비밀번호"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              autoComplete="current-password"
            />
            <Input
              type="password"
              placeholder="새 비밀번호 (6자 이상)"
              value={next}
              onChange={(e) => setNext(e.target.value)}
              autoComplete="new-password"
            />
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "변경 중…" : "비밀번호 변경"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Button variant="outline" className="w-full" onClick={onLogout}>
        로그아웃
      </Button>
    </div>
  );
}
