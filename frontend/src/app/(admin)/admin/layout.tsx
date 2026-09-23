import type { ReactNode } from "react";

export const metadata = {
  robots: { index: false, follow: false },
};

export default function AdminRootLayout({ children }: { children: ReactNode }) {
  return <div className="min-h-full bg-background">{children}</div>;
}
