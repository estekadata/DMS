import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Multirex Auto DMS",
  description: "Système de gestion intelligent",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className={`${inter.className} h-full antialiased`}>
      <body className="min-h-full bg-gray-50">
        {children}
        <Toaster position="top-right" />
      </body>
    </html>
  );
}
