"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

type Tab = "Stock" | "Prix" | "Tendances" | "Offres";

const COLORS = ["#C41E3A", "#F87171", "#FBBF24", "#34D399", "#60A5FA", "#A78BFA", "#FB923C", "#F472B6"];

const tooltipStyle = { background: "#FFFFFF", border: "1px solid #E5E7EB", borderRadius: 10, color: "#111827", boxShadow: "0 4px 12px rgba(0,0,0,0.08)" };

// Helper: récupère toutes les lignes en paginant (dépasse la limite Supabase de 1000/5000)
async function fetchAll<T = any>(buildQuery: (from: number, to: number) => any, maxTotal = 50000): Promise<T[]> {
  const all: T[] = [];
  const pageSize = 5000;
  let from = 0;
  while (from < maxTotal) {
    const { data, error } = await buildQuery(from, from + pageSize - 1);
    if (error || !data || data.length === 0) break;
    all.push(...data);
    if (data.length < pageSize) break;
    from += pageSize;
  }
  return all;
}

function ChartHeader({ title, total, unit }: { title: string; total: number; unit: string }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <h3 className="font-semibold text-foreground">{title}</h3>
      <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-brand-soft text-brand tabular-nums">
        {total.toLocaleString("fr-FR")} {unit}
      </span>
    </div>
  );
}

export default function AnalysePage() {
  const [tab, setTab] = useState<Tab>("Stock");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setData(null); // Reset pour éviter de réutiliser les données du tab précédent
      if (tab === "Stock") {
        // Pagination pour dépasser la limite Supabase
        const moteurs = await fetchAll((from, to) =>
          supabase
            .from("v_moteurs_dispo")
            .select("marque, energie")
            .eq("est_disponible", 1)
            .range(from, to)
        );

        const byMarque: Record<string, number> = {};
        const byEnergie: Record<string, number> = {};
        (moteurs || []).forEach((m: any) => {
          const marque = m.marque || "Inconnu";
          const energie = m.energie || "Inconnu";
          byMarque[marque] = (byMarque[marque] || 0) + 1;
          byEnergie[energie] = (byEnergie[energie] || 0) + 1;
        });
        setData({
          totalStock: (moteurs || []).length,
          topMarques: Object.entries(byMarque).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([name, value]) => ({ name, value })),
          byEnergie: Object.entries(byEnergie).map(([name, value]) => ({ name, value })),
        });
      } else if (tab === "Prix") {
        const moteurs = await fetchAll((from, to) =>
          supabase
            .from("v_moteurs_dispo")
            .select("marque, nom_type_moteur, prix_achat_moteur")
            .eq("est_disponible", 1)
            .gt("prix_achat_moteur", 0)
            .range(from, to)
        );

        // Prix moyen par marque
        const byMarque: Record<string, { total: number; count: number }> = {};
        // Prix moyen par type moteur (ex: K9K, 9HO, DV6TED4)
        const byType: Record<string, { total: number; count: number }> = {};

        (moteurs || []).forEach((m: any) => {
          const p = m.prix_achat_moteur || 0;
          const marque = (m.marque || "Inconnu").toUpperCase();
          byMarque[marque] = byMarque[marque] || { total: 0, count: 0 };
          byMarque[marque].total += p;
          byMarque[marque].count++;

          const raw = (m.nom_type_moteur || "").trim();
          const type = raw.split(/[\s\-]+/)[0].toUpperCase();
          if (type && type.length >= 2) {
            byType[type] = byType[type] || { total: 0, count: 0 };
            byType[type].total += p;
            byType[type].count++;
          }
        });

        const prixParMarque = Object.entries(byMarque)
          .filter(([, v]) => v.count >= 3) // éviter le bruit (marques avec 1-2 moteurs)
          .map(([marque, v]) => ({ name: marque, prixMoyen: Math.round(v.total / v.count), nb: v.count }))
          .sort((a, b) => b.prixMoyen - a.prixMoyen)
          .slice(0, 10);

        const prixParType = Object.entries(byType)
          .filter(([, v]) => v.count >= 3)
          .map(([type, v]) => ({ name: type, prixMoyen: Math.round(v.total / v.count), nb: v.count }))
          .sort((a, b) => b.prixMoyen - a.prixMoyen)
          .slice(0, 15);

        const avg = (moteurs || []).reduce((s: number, m: any) => s + (m.prix_achat_moteur || 0), 0) / ((moteurs || []).length || 1);
        setData({ prixParMarque, prixParType, avg: Math.round(avg), totalPrix: (moteurs || []).length });
      } else if (tab === "Tendances") {
        const cutoff = new Date();
        cutoff.setMonth(cutoff.getMonth() - 12);
        const cutoffIso = cutoff.toISOString();
        const [recData, expData] = await Promise.all([
          fetchAll((from, to) =>
            supabase.from("v_receptions")
              .select("date_reception, nb_moteurs")
              .gte("date_reception", cutoffIso)
              .range(from, to)
          ),
          fetchAll((from, to) =>
            supabase.from("tbl_expeditions_moteurs")
              .select("date_validation, prix_vente_moteur")
              .gte("date_validation", cutoffIso)
              .range(from, to)
          ),
        ]);
        const byMonth: Record<string, { mois: string; recus: number; vendus: number; ca: number }> = {};
        (recData || []).forEach((r: any) => {
          const k = r.date_reception?.substring(0, 7) || "";
          if (!byMonth[k]) byMonth[k] = { mois: k, recus: 0, vendus: 0, ca: 0 };
          byMonth[k].recus += r.nb_moteurs || 0;
        });
        (expData || []).forEach((e: any) => {
          const k = e.date_validation?.substring(0, 7) || "";
          if (!byMonth[k]) byMonth[k] = { mois: k, recus: 0, vendus: 0, ca: 0 };
          byMonth[k].vendus++;
          byMonth[k].ca += e.prix_vente_moteur || 0;
        });
        const monthsArr = Object.values(byMonth).sort((a, b) => a.mois.localeCompare(b.mois));
        const totalRecus = monthsArr.reduce((s, m) => s + m.recus, 0);
        const totalVendus = monthsArr.reduce((s, m) => s + m.vendus, 0);
        setData({ months: monthsArr, totalRecus, totalVendus });
      } else {
        // Récupérer toutes les expéditions (avec pagination)
        const topSales = await fetchAll((from, to) =>
          supabase
            .from("tbl_expeditions_moteurs")
            .select("n_moteur, prix_vente_moteur")
            .not("n_moteur", "is", null)
            .range(from, to)
        );

        const motorIds = [...new Set((topSales || []).map((e: any) => e.n_moteur).filter(Boolean))] as number[];
        const codeByMotor: Record<number, string> = {};
        // Batch IN queries pour éviter URL trop longues
        const batchSize = 500;
        for (let i = 0; i < motorIds.length; i += batchSize) {
          const batch = motorIds.slice(i, i + batchSize);
          const { data: motors } = await supabase
            .from("v_moteurs_dispo")
            .select("n_moteur, nom_type_moteur")
            .in("n_moteur", batch);
          (motors || []).forEach((m: any) => {
            const raw = (m.nom_type_moteur || "").trim();
            const code = raw.split(/[\s\-]+/)[0].toUpperCase();
            if (code && code.length >= 2) codeByMotor[m.n_moteur] = code;
          });
        }

        const codeMap: Record<string, { ventes: number; ca: number }> = {};
        (topSales || []).forEach((e: any) => {
          const k = codeByMotor[e.n_moteur];
          if (!k) return;
          if (!codeMap[k]) codeMap[k] = { ventes: 0, ca: 0 };
          codeMap[k].ventes++;
          codeMap[k].ca += e.prix_vente_moteur || 0;
        });
        setData({
          totalVentes: (topSales || []).length,
          topOffres: Object.entries(codeMap)
            .sort((a, b) => b[1].ventes - a[1].ventes)
            .slice(0, 15)
            .map(([code, v]) => ({ code, ...v, ca: Math.round(v.ca) })),
        });
      }
      setLoading(false);
    }
    load();
  }, [tab]);

  return (
    <div>
      <PageHeader title="Analyse avancée" description="Statistiques détaillées du stock et des ventes" />

      <div className="flex bg-surface-alt rounded-lg border border-border overflow-hidden mb-6 w-fit">
        {(["Stock", "Prix", "Tendances", "Offres"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-5 py-2 text-sm font-medium transition-all ${tab === t ? "bg-brand text-white" : "text-text-dim hover:bg-surface-hover"}`}
          >
            {t}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-16 text-text-muted">Chargement...</div>
      ) : tab === "Stock" && data && data.topMarques && data.byEnergie ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-surface border border-border rounded-[14px] p-6">
            <ChartHeader title="Stock disponible par marque (Top 10)" total={data.totalStock ?? 0} unit="moteurs" />
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.topMarques} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis type="number" tick={{ fontSize: 11, fill: "#4B5563" }} />
                <YAxis dataKey="name" type="category" width={80} tick={{ fontSize: 11, fill: "#4B5563" }} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="value" fill="#C41E3A" radius={[0, 4, 4, 0]} name="Disponibles" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="bg-surface border border-border rounded-[14px] p-6">
            <ChartHeader title="Répartition par énergie" total={data.totalStock ?? 0} unit="moteurs" />
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={data.byEnergie} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}>
                  {data.byEnergie.map((_: any, i: number) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : tab === "Prix" && data && data.prixParMarque ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-surface border border-border rounded-[14px] p-6 flex flex-col justify-center items-center">
              <p className="text-text-dim text-sm mb-2">Prix d&apos;achat moyen</p>
              <p className="text-4xl font-bold text-brand">{(data.avg ?? 0).toLocaleString("fr-FR")} €</p>
              <p className="text-xs text-text-muted mt-2">sur {(data.totalPrix ?? 0).toLocaleString("fr-FR")} moteurs</p>
            </div>
            <div className="bg-surface border border-border rounded-[14px] p-6 md:col-span-2">
              <ChartHeader title="Prix moyen par marque (Top 10)" total={data.prixParMarque?.length ?? 0} unit="marques" />
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={data.prixParMarque} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis type="number" tick={{ fontSize: 11, fill: "#4B5563" }} tickFormatter={(v) => `${v} €`} />
                  <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 11, fill: "#4B5563" }} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(value: any, _name, props) => [`${value} € (${props.payload.nb} moteurs)`, "Prix moyen"]} />
                  <Bar dataKey="prixMoyen" fill="#C41E3A" radius={[0, 4, 4, 0]} name="Prix moyen" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="bg-surface border border-border rounded-[14px] p-6">
            <ChartHeader title="Prix moyen par type moteur (Top 15)" total={data.prixParType?.length ?? 0} unit="types" />
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.prixParType}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#4B5563" }} />
                <YAxis tick={{ fontSize: 12, fill: "#4B5563" }} tickFormatter={(v) => `${v} €`} />
                <Tooltip contentStyle={tooltipStyle} formatter={(value: any, _name, props) => [`${value} € (${props.payload.nb} moteurs)`, "Prix moyen"]} />
                <Bar dataKey="prixMoyen" fill="#C41E3A" radius={[4, 4, 0, 0]} name="Prix moyen" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : tab === "Tendances" && data && data.months ? (
        <div className="bg-surface border border-border rounded-[14px] p-6">
          <ChartHeader title="Réceptions vs Ventes — 12 derniers mois" total={(data.totalRecus ?? 0) + (data.totalVendus ?? 0)} unit="mouvements" />
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.months}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="mois" tick={{ fontSize: 11, fill: "#4B5563" }} />
              <YAxis tick={{ fontSize: 12, fill: "#4B5563" }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ color: "#4B5563" }} />
              <Bar dataKey="recus" fill="#60A5FA" radius={[4, 4, 0, 0]} name="Reçus" />
              <Bar dataKey="vendus" fill="#C41E3A" radius={[4, 4, 0, 0]} name="Vendus" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : tab === "Offres" && data && data.topOffres ? (
        <div className="bg-surface border border-border rounded-[14px] p-6">
          <ChartHeader title="Top 15 références les plus vendues" total={data.totalVentes ?? 0} unit="ventes" />
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.topOffres}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="code" tick={{ fontSize: 11, fill: "#4B5563" }} />
              <YAxis tick={{ fontSize: 12, fill: "#4B5563" }} />
              <Tooltip contentStyle={tooltipStyle} formatter={(value, name) => [name === "ca" ? `${Number(value).toLocaleString("fr-FR")} €` : value, name === "ca" ? "CA" : "Ventes"]} />
              <Legend wrapperStyle={{ color: "#4B5563" }} />
              <Bar dataKey="ventes" fill="#C41E3A" radius={[4, 4, 0, 0]} name="Ventes" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : null}
    </div>
  );
}
