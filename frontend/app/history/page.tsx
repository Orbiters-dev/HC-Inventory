"use client";

import { useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BASE_PATH } from "@/lib/constants";

interface LogRow {
  id: number;
  created_at: string;
  amazon_category: string;
  walmart_category: string;
  estimated_price_amz: string;
  estimated_price_wmt: string;
}

export default function HistoryPage() {
  const [rows, setRows] = useState<LogRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${BASE_PATH}/api/calculation-logs/`, { credentials: "include" })
      .then((r) => r.json())
      .then((d) => setRows(d.results ?? d ?? []))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="mx-auto max-w-4xl p-6">
      <Card>
        <CardHeader>
          <CardTitle>계산 이력</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-muted-foreground text-sm">로딩 중…</p>
          ) : rows.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              아직 계산 이력이 없습니다.
            </p>
          ) : (
            <div className="space-y-1 text-sm">
              {rows.map((r) => (
                <div
                  key={r.id}
                  className="flex flex-wrap justify-between gap-2 border-b py-2"
                >
                  <span className="text-muted-foreground">
                    {new Date(r.created_at).toLocaleString("ko-KR")}
                  </span>
                  <span>
                    아마존 {r.amazon_category} · 월마트 {r.walmart_category}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
