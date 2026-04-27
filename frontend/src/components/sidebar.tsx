"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, TrendingUp, Target, BarChart3, Euro,
  PackageOpen, Search, Cog, ClipboardList, History,
  Wrench, Building2, Users, LogOut, DatabaseZap,
} from "lucide-react";

const navSections = [
  {
    title: "Commercial",
    items: [
      { label: "Ventes", href: "/ventes", icon: TrendingUp },
      { label: "Besoins", href: "/besoins", icon: Target },
      { label: "Analyse", href: "/analyse", icon: BarChart3 },
      { label: "Mise à jour prix", href: "/prix", icon: Euro },
    ],
  },
  {
    title: "Gestion interne",
    items: [
      { label: "Réceptions", href: "/receptions", icon: PackageOpen },
      { label: "Moteurs", href: "/moteurs", icon: Search },
      { label: "Boîtes", href: "/boites", icon: Cog },
      { label: "Réservations", href: "/reservations", icon: ClipboardList },
      { label: "Historique", href: "/historique", icon: History },
    ],
  },
  {
    title: "Outils",
    items: [
      { label: "Pièces détachées", href: "/pieces", icon: Wrench },
      { label: "Centres VHU", href: "/vhu", icon: Building2 },
    ],
  },
];

interface SidebarProps {
  userName?: string;
  userRole?: string;
}

export function Sidebar({ userName, userRole }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();

  const roleLabel = { super_admin: "Super Admin", admin: "Admin", vhu: "VHU" }[userRole || "admin"] || userRole;

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/");
  }

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 bg-surface border-r border-border flex flex-col">
      {/* Header */}
      <div className="p-6 text-center border-b border-border">
        <h1 className="font-heading text-lg font-bold tracking-wide text-foreground">MULTIREX AUTO</h1>
        {userName && (
          <p className="text-xs mt-1 text-text-dim">{userName} ({roleLabel})</p>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
        {/* Home */}
        <Link
          href="/dashboard"
          className={cn(
            "flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all",
            pathname === "/dashboard"
              ? "bg-brand-soft text-brand"
              : "text-text-dim hover:bg-surface-hover hover:text-foreground"
          )}
        >
          <LayoutDashboard size={18} /> Tableau de bord
        </Link>

        {navSections.map((section) => (
          <div key={section.title}>
            <p className="px-4 text-[10px] font-bold uppercase tracking-[0.06em] text-text-muted mb-2">
              {section.title}
            </p>
            <div className="space-y-1">
              {section.items.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all",
                    pathname === item.href
                      ? "bg-brand-soft text-brand"
                      : "text-text-dim hover:bg-surface-hover hover:text-foreground"
                  )}
                >
                  <item.icon size={18} /> {item.label}
                </Link>
              ))}
            </div>
          </div>
        ))}

        {userRole === "super_admin" && (
          <div>
            <p className="px-4 text-[10px] font-bold uppercase tracking-[0.06em] text-text-muted mb-2">
              Administration
            </p>
            <Link
              href="/admin/utilisateurs"
              className={cn(
                "flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all",
                pathname === "/admin/utilisateurs"
                  ? "bg-brand-soft text-brand"
                  : "text-text-dim hover:bg-surface-hover hover:text-foreground"
              )}
            >
              <Users size={18} /> Utilisateurs
            </Link>
            <Link
              href="/admin/import-donnees"
              className={cn(
                "flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all",
                pathname === "/admin/import-donnees"
                  ? "bg-brand-soft text-brand"
                  : "text-text-dim hover:bg-surface-hover hover:text-foreground"
              )}
            >
              <DatabaseZap size={18} /> Import données
            </Link>
          </div>
        )}
      </nav>

      {/* Logout */}
      <div className="p-4 border-t border-border">
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-text-dim bg-surface-alt hover:bg-surface-hover transition-all"
        >
          <LogOut size={16} /> Se déconnecter
        </button>
      </div>
    </aside>
  );
}
