"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { KpiCard } from "@/components/kpi-card";
import { KPI_CATALOG, DEFAULT_KPIS, type DashboardKpis } from "@/lib/types";
import { Skeleton } from "@/components/ui/skeleton";
import { getDashboardKpis } from "@/lib/queries/dashboard";
import {
  TrendingUp, Target, BarChart3, Euro,
  PackageOpen, Search, Cog, ClipboardList,
  History, Wrench, Building2,
} from "lucide-react";

const navGrid = [
  { title: "Commercial", items: [
    { label: "Ventes", desc: "Analyse des ventes", href: "/ventes", icon: TrendingUp },
    { label: "Besoins", desc: "Besoins centres VHU", href: "/besoins", icon: Target },
    { label: "Analyse", desc: "Statistiques", href: "/analyse", icon: BarChart3 },
    { label: "Mise a jour prix", desc: "Propositions achat", href: "/prix", icon: Euro },
  ]},
  { title: "Gestion interne", items: [
    { label: "Receptions", desc: "Gestion des arrivages", href: "/receptions", icon: PackageOpen },
    { label: "Moteurs", desc: "Identification moteurs", href: "/moteurs", icon: Search },
    { label: "Boites", desc: "Identification BV", href: "/boites", icon: Cog },
    { label: "Reservations", desc: "Reservations clients", href: "/reservations", icon: ClipboardList },
  ]},
  { title: "Outils", items: [
    { label: "Historique", desc: "Receptions & expeditions", href: "/historique", icon: History },
    { label: "Pieces Detachees", desc: "Stock alternateurs...", href: "/pieces", icon: Wrench },
    { label: "Centres VHU", desc: "Interface centres VHU", href: "/vhu", icon: Building2 },
  ]},
];

export default function DashboardPage() {
  const [kpis, setKpis] = useState<DashboardKpis | null>(null);

  useEffect(() => {
    getDashboardKpis().then(setKpis).catch(console.error);
  }, []);

  return (
    <div>
      <div className="text-center mb-8">
        <h1 className="font-heading text-3xl font-bold text-foreground">Tableau de bord</h1>
        <p className="text-text-dim mt-1 text-sm">Choisissez une section pour commencer</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {kpis
          ? DEFAULT_KPIS.map((key) => (
              <KpiCard key={key} meta={KPI_CATALOG[key]} value={kpis[key as keyof DashboardKpis] as number} />
            ))
          : Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-[14px] bg-surface-alt" />
            ))}
      </div>

      {/* Tendance */}
      {kpis && (() => {
        const deltaVentes = (kpis.ventes_mois ?? 0) - (kpis.ventes_mois_prec ?? 0);
        const deltaCa = (kpis.ca_mois ?? 0) - (kpis.ca_mois_prec ?? 0);
        return (
          <div className="bg-surface border border-border rounded-[14px] px-5 py-3 mb-8 flex gap-6 text-sm text-text-dim">
            <span>Tendance vs mois precedent :</span>
            <span className={deltaVentes >= 0 ? "text-emerald-600 font-semibold" : "text-red-600 font-semibold"}>
              {deltaVentes >= 0 ? "+" : ""}{deltaVentes} ventes
            </span>
            <span className={deltaCa >= 0 ? "text-emerald-600 font-semibold" : "text-red-600 font-semibold"}>
              {deltaCa >= 0 ? "+" : ""}{Math.round(deltaCa).toLocaleString("fr-FR")} EUR CA
            </span>
          </div>
        );
      })()}

      {/* Navigation Grid */}
      {navGrid.map((section) => (
        <div key={section.title} className="mb-8">
          <h2 className="text-base font-semibold text-text-dim mb-3">{section.title}</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {section.items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="bg-surface border border-border rounded-[14px] p-5 hover:bg-surface-hover hover:-translate-y-0.5 transition-all group"
              >
                <div className="mb-3 text-brand group-hover:scale-110 transition-transform">
                  <item.icon size={28} strokeWidth={1.8} />
                </div>
                <h3 className="font-semibold text-foreground">{item.label}</h3>
                <p className="text-xs text-text-dim mt-1">{item.desc}</p>
              </Link>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
