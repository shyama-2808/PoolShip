import type { Metadata } from "next";
import Navbar from "@/components/layout/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "PoolShip - Peer-to-Peer Freight Pooling for MSMEs",
  description:
    "Share truck capacity along common routes, split freight costs transparently, and cut carbon emissions.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="max-w-full overflow-x-hidden">
      <body className="min-h-screen flex flex-col bg-slate-50 text-slate-900 antialiased max-w-full overflow-x-hidden">
        <Navbar />
        <main className="flex-1 w-full max-w-full overflow-x-clip">{children}</main>
        <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
          <p>© 2026 PoolShip Technologies. Built for Indian MSMEs & Green Logistics.</p>
        </footer>
      </body>
    </html>
  );
}

