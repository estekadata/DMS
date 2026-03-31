"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { KpiCard } from "@/components/kpi-card";
import { KPI_CATALOG, DEFAULT_KPIS, type DashboardKpis } from "@/lib/types";
import { Skeleton } from "@/components/ui/skeleton";
import { getDashboardKpis } from "@/lib/queries/dashboard";

const navGrid = [
  { title: "Commercial", items: [
    { label: "Ventes", desc: "Analyse des ventes", href: "/ventes", icon: "📈" },
    { label: "Besoins", desc: "Besoins centres VHU", href: "/besoins", icon: "🎯" },
    { label: "Analyse", desc: "Statistiques", href: "/analyse", icon: "📊" },
    { label: "Mise a jour prix", desc: "Propositions achat", href: "/prix", icon: "💶" },
  ]},
  { title: "Gestion interne", items: [
    { label: "Receptions", desc: "Gestion des arrivages", href: "/receptions", icon: "📥" },
    { label: "Moteurs", desc: "Identification moteurs", href: "/moteurs", icon: "🔍" },
    { label: "Boites", desc: "Identification BV", href: "/boites", icon: "⚙️" },
    { label: "Reservations", desc: "Reservations clients", href: "/reservations", icon: "📋" },
  ]},
  { title: "Outils", items: [
    { label: "Historique", desc: "Receptions & expeditions", href: "/historique", icon: "📜" },
    { label: "Pieces Detachees", desc: "Stock alternateurs...", href: "/pieces", icon: "🔩" },
    { label: "Centres VHU", desc: "Interface centres VHU", href: "/vhu", icon: "🛠️" },
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
        <h1 className="text-3xl font-bold text-gray-900">Tableau de bord</h1>
        <p className="text-gray-500 mt-1">Choisissez une section pour commencer</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {kpis
          ? DEFAULT_KPIS.map((key) => (
              <KpiCard key={key} meta={KPI_CATALOG[key]} value={kpis[key as keyof DashboardKpis] as number} />
            ))
          : Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-2xl" />
            ))}
      </div>

      {/* Tendance */}
      {kpis && (
        <div className="bg-white rounded-xl px-5 py-3 mb-8 flex gap-6 text-sm text-gray-500 shadow-sm">
          <span>Tendance vs mois precedent :</span>
          <span className={kpis.ventes_mois - kpis.ventes_mois_prec >= 0 ? "text-emerald-600 font-semibold" : "text-red-600 font-semibold"}>
            {kpis.ventes_mois - kpis.ventes_mois_prec >= 0 ? "+" : ""}{kpis.ventes_mois - kpis.ventes_mois_prec} ventes
          </span>
          <span className={kpis.ca_mois - kpis.ca_mois_prec >= 0 ? "text-emerald-600 font-semibold" : "text-red-600 font-semibold"}>
            {kpis.ca_mois - kpis.ca_mois_prec >= 0 ? "+" : ""}{Math.round(kpis.ca_mois - kpis.ca_mois_prec).toLocaleString("fr-FR")} EUR CA
          </span>
        </div>
      )}

      {/* Navigation Grid */}
      {navGrid.map((section) => (
        <div key={section.title} className="mb-8">
          <h2 className="text-lg font-semibold text-gray-700 mb-3">{section.title}</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {section.items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md hover:-translate-y-0.5 transition-all group"
              >
                <div className="text-3xl mb-3 group-hover:scale-110 transition-transform">{item.icon}</div>
                <h3 className="font-semibold text-gray-900">{item.label}</h3>
                <p className="text-xs text-gray-500 mt-1">{item.desc}</p>
              </Link>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
