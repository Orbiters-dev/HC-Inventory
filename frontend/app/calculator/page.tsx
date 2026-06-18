"use client";

/**
 * Calculator 페이지 — url_swap plan v9 Phase 1.1.
 *
 * ONZ APP `pages/calculator.js` 의 dashboard 흡수.
 * source: Orbiters11-dev/MVP/export_calculator_frontend.
 * dynamic import 로 SSR 제외 + initial bundle 영향 0.
 */
import dynamic from "next/dynamic";

const CalculatorForm = dynamic(() => import("./_components/CalculatorForm"), {
  ssr: false,
  loading: () => <div className="p-6">Loading…</div>,
});

export default function CalculatorPage() {
  return <CalculatorForm />;
}
