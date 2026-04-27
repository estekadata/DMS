import type { Metadata } from "next";
import { DM_Sans, Fraunces } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const dmSans = DM_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-sans",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["400", "600", "700", "900"],
  variable: "--font-heading",
});

export const metadata: Metadata = {
  title: "Multirex Auto DMS",
  description: "Système de gestion intelligent",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className={`${dmSans.variable} ${fraunces.variable} h-full`}>
      <body className="min-h-full bg-background text-foreground font-sans antialiased">
        {children}
        <Toaster position="top-right" />
      </body>
    </html>
  );
}
