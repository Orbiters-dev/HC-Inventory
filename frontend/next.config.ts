import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // standalone 번들(.next/standalone) — 로컬빌드+rsync 배포(OOM 회피).
  output: "standalone",
  // sharp darwin↔linux 불일치 회피(계산기는 이미지 최적화 불필요).
  images: { unoptimized: true },
  // same-origin: nginx 가 /api/·/auth/ → Django(8010) 프록시. basePath 없음(root mount).
  // Next 16 은 build 단계 ESLint 미실행(별도 eslint CLI) — P8 에서 CI 구성.
};

export default nextConfig;
