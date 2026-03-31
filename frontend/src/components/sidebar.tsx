"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

const navSections = [
  {
    title: "Commercial",
    items: [
      { label: "Ventes", href: "/ventes", icon: "📈" },
      { label: "Besoins", href: "/besoins", icon: "🎯" },
      { label: "Analyse", href: "/analyse", icon: "📊" },
      { label: "Mise à jour prix", href: "/prix", icon: "💶" },
    ],
  },
  {
    title: "Gestion interne",
    items: [
      { label: "Réceptions", href: "/receptions", icon: "📥" },
      { label: "Moteurs", href: "/moteurs", icon: "🔍" },
      { label: "Boîtes", href: "/boites", icon: "⚙️" },
      { label: "Réservations", href: "/reservations", icon: "📋" },
      { label: "Historique", href: "/historique", icon: "📜" },
    ],
  },
  {
    title: "Outils",
    items: [
      { label: "Pièces détachées", href: "/pieces", icon: "🔩" },
      { label: "Centres VHU", href: "/vhu", icon: "🛠️" },
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
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 bg-gradient-to-b from-[#C41E3A] to-[#8B1A2B] text-white flex flex-col">
      {/* Header */}
      <div className="p-6 text-center border-b border-white/10">
        <h1 className="text-lg font-bold tracking-wide">MULTIREX AUTO</h1>
        {userName && (
          <p className="text-xs mt-1 opacity-80">{userName} ({roleLabel})</p>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
        {/* Home */}
        <Link
          href="/dashboard"
          className={cn(
            "flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all",
            pathname === "/dashboard"
              ? "bg-white/20 shadow-lg"
              : "hover:bg-white/10"
          )}
        >
          <span>🏠</span> Tableau de bord
        </Link>

        {navSections.map((section) => (
          <div key={section.title}>
            <p className="px-4 text-[11px] font-semibold uppercase tracking-wider opacity-60 mb-2">
              {section.title}
            </p>
            <div className="space-y-1">
              {section.items.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all",
                    pathname === item.href
                      ? "bg-white/20 shadow-lg"
                      : "hover:bg-white/10"
                  )}
                >
                  <span>{item.icon}</span> {item.label}
                </Link>
              ))}
            </div>
          </div>
        ))}

        {userRole === "super_admin" && (
          <div>
            <p className="px-4 text-[11px] font-semibold uppercase tracking-wider opacity-60 mb-2">
              Administration
            </p>
            <Link
              href="/admin/utilisateurs"
              className={cn(
                "flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all",
                pathname === "/admin/utilisateurs"
                  ? "bg-white/20 shadow-lg"
                  : "hover:bg-white/10"
              )}
            >
              <span>👥</span> Utilisateurs
            </Link>
          </div>
        )}
      </nav>

      {/* Logout */}
      <div className="p-4 border-t border-white/10">
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium bg-white/10 hover:bg-white/20 transition-all"
        >
          🚪 Se déconnecter
        </button>
      </div>
    </aside>
  );
}
