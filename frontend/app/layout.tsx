import type { Metadata } from "next";
import { Toaster } from "sonner";

import { AuthGate } from "@/components/auth-gate";

import "./globals.css";

export const metadata: Metadata = {
  title: "수출 비용 계산기",
  description: "HC-Inventory — 수출 비용 계산기",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>
        <AuthGate>{children}</AuthGate>
        <Toaster richColors position="top-center" />
      </body>
    </html>
  );
}
