/**
 * 재고 리포트 탭 — ORBITOOL 재고관리 모듈 주간 리포트(정적 HTML)를 임베드.
 *
 * 리포트 본문은 public/inventory-report.html (매주 새 리포트로 교체 후 push 하면
 * 자동배포로 갱신). AuthGate 안에 있어 로그인해야 이 탭 진입 가능.
 */
export default function InventoryPage() {
  return (
    <iframe
      src="/inventory-report.html"
      title="재고 리포트"
      className="h-[calc(100dvh-49px)] w-full border-0 md:h-screen"
    />
  );
}
