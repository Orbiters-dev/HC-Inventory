"use client";

// Route-segment error boundary for /calculator.
// Calculator form 의 dynamic import / 환율 조회 / 계산식 throw 가 전체
// 대시보드를 다운시키지 않게 한다. (dashboard)/error.tsx 의 group-level
// fallback 보다 한 단계 친절한 영역별 안내 + retry 제공.

import { Button } from "@/components/ui/button";

export default function CalculatorError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 p-6 text-center">
      <h2 className="text-lg font-semibold text-foreground">
        계산기 화면을 불러오는 중 문제가 발생했습니다.
      </h2>
      <p className="max-w-md text-sm text-muted-foreground">
        환율 / 수수료 데이터 또는 계산 폼 로딩에 실패했습니다. 입력하신 값은
        브라우저에 남아있을 수 있으니, 다시 시도하거나 새로고침해 주세요.
      </p>
      {error.digest ? (
        <code className="rounded bg-muted px-2 py-1 text-xs text-muted-foreground">
          digest: {error.digest}
        </code>
      ) : null}
      <div className="flex gap-2">
        <Button onClick={reset} variant="default" size="sm">
          다시 시도
        </Button>
        <Button
          onClick={() => window.location.reload()}
          variant="outline"
          size="sm"
        >
          새로고침
        </Button>
      </div>
    </div>
  );
}
