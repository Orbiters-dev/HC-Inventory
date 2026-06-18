// HC-Inventory ESLint flat config (ESLint v9 + eslint-config-next 16).
// next/core-web-vitals + typescript 규칙을 사용. CI lint 게이트(.github/workflows/ci.yml)가 실행.
import coreWebVitals from "eslint-config-next/core-web-vitals";
import typescript from "eslint-config-next/typescript";

/** @type {import('eslint').Linter.Config[]} */
const config = [
  ...coreWebVitals,
  ...typescript,
  {
    ignores: [".next/**", "next-env.d.ts", "node_modules/**"],
  },
];

export default config;
