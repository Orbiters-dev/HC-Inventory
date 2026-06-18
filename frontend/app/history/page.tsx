"use client";

import { useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BASE_PATH } from "@/lib/constants";
import { INPUT_FIELDS, RESULT_FIELDS } from "@/lib/result-labels";

interface LogRow {
  id: number;
  created_at: string;
  amazon_category: string;
  walmart_category: string;
  product_name?: string;
}

type LogDetail = Record<string, string | number | null>;

export default function HistoryPage() {
  const [rows, setRows] = useState<LogRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<LogDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    fetch(`${BASE_PATH}/api/calculation-logs/`, { credentials: "include" })
      .then((r) => r.json())
      .then((d) => setRows(d.results ?? d ?? []))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, []);

  async function toggle(id: number) {
    // 같은 항목 재클릭 = 접기(중복 fetch 방지). 다른 항목 = 새로 불러오기.
    if (expandedId === id) {
      setExpandedId(null);
      setDetail(null);
      return;
    }
    setExpandedId(id);
    setDetail(null);
    setDetailLoading(true);
    try {
      const r = await fetch(`${BASE_PATH}/api/calculation-logs/${id}/`, {
        credentials: "include",
      });
      setDetail(await r.json());
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }

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
            <div className="text-sm">
              {rows.map((r) => (
                <div key={r.id} className="border-b last:border-b-0">
                  <button
                    type="button"
                    onClick={() => toggle(r.id)}
                    aria-expanded={expandedId === r.id}
                    className="hover:bg-accent/40 flex w-full flex-wrap items-center gap-2 px-1 py-2 text-left"
                  >
                    <span className="text-muted-foreground shrink-0">
                      {new Date(r.created_at).toLocaleString("ko-KR")}
                    </span>
                    <span className="min-w-0 flex-1 truncate font-medium">
                      {r.product_name ||
                        `아마존 ${r.amazon_category} · 월마트 ${r.walmart_category}`}
                    </span>
                    <span className="text-muted-foreground shrink-0 text-xs">
                      {expandedId === r.id ? "▲ 접기" : "▼ 상세"}
                    </span>
                  </button>
                  {expandedId === r.id && (
                    <div className="pb-3">
                      {detailLoading ? (
                        <p className="text-muted-foreground px-1 py-2 text-sm">
                          불러오는 중…
                        </p>
                      ) : detail ? (
                        <LogDetailView d={detail} />
                      ) : (
                        <p className="text-muted-foreground px-1 py-2 text-sm">
                          상세를 불러오지 못했습니다.
                        </p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function LogDetailView({ d }: { d: LogDetail }) {
  return (
    <div className="bg-muted/30 space-y-4 rounded-md p-4">
      <Section
        title="입력"
        fields={INPUT_FIELDS.map((f) => ({ label: f.label, value: d[f.snake] }))}
      />
      <Section
        title="결과"
        fields={RESULT_FIELDS.map((f) => ({
          label: f.label,
          value: d[f.snake],
        }))}
      />
      {d.memo ? (
        <div>
          <div className="text-muted-foreground mb-1 text-xs font-semibold">
            메모
          </div>
          <p className="text-sm whitespace-pre-wrap">{String(d.memo)}</p>
        </div>
      ) : null}
    </div>
  );
}

function Section({
  title,
  fields,
}: {
  title: string;
  fields: { label: string; value: unknown }[];
}) {
  const shown = fields.filter(
    (f) => f.value !== undefined && f.value !== null && f.value !== "",
  );
  if (shown.length === 0) return null;
  return (
    <div>
      <div className="text-muted-foreground mb-1 text-xs font-semibold">
        {title}
      </div>
      <div className="grid gap-x-4 gap-y-1 sm:grid-cols-2">
        {shown.map((f) => (
          <div
            key={f.label}
            className="border-border/50 flex justify-between border-b border-dashed py-0.5 text-sm"
          >
            <span className="text-muted-foreground">{f.label}</span>
            <span className="font-mono">{String(f.value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
