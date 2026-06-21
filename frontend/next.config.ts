import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // standalone 번들(.next/standalone) — 로컬빌드+rsync 배포(OOM 회피).
  output: "standalone",
  // sharp darwin↔linux 불일치 회피(계산기는 이미지 최적화 불필요).
  images: { unoptimized: true },
  // /inventory → 재고 리포트(public 정적 HTML) 를 최상위로 직접 서빙.
  // iframe 임베드는 리포트 응답의 X-Frame-Options: DENY 때문에 차단되므로,
  // rewrite 로 /inventory URL 에서 리포트를 그대로(top-level) 보여준다.
  async rewrites() {
    return [{ source: "/inventory", destination: "/inventory-report.html" }];
  },
  // same-origin: nginx 가 /api/·/auth/ → Django(8010) 프록시. basePath 없음(root mount).
  // Next 16 은 build 단계 ESLint 미실행(별도 eslint CLI) — P8 에서 CI 구성.
};

export default nextConfig;
