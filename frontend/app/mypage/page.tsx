"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { BASE_PATH } from "@/lib/constants";
import { getCSRFToken } from "@/lib/csrf";

export default function MyPage() {
  const router = useRouter();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [loading, setLoading] = useState(false);

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
    await fetch(`${BASE_PATH}/auth/logout/`, {
      method: "POST",
      credentials: "include",
      headers: { "X-CSRFToken": getCSRFToken() },
    });
    router.replace("/login");
  }

  return (
    <div className="mx-auto max-w-sm p-6">
      <Card>
        <CardHeader>
          <CardTitle>마이페이지 — 비밀번호 변경</CardTitle>
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
          <Button variant="outline" className="mt-3 w-full" onClick={onLogout}>
            로그아웃
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
