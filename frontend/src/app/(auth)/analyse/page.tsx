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

const COLORS = ["#C41E3A", "#8B1A2B", "#E8526A", "#F4A0B0", "#2563EB", "#16A34A", "#D97706", "#7C3AED"];

export default function AnalysePage() {
  const [tab, setTab] = useState<Tab>("Stock");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      if (tab === "Stock") {
        const { data: moteurs } = await supabase
          .from("v_moteurs_dispo")
          .select("marque, energie, est_disponible")
          .limit(2000);

        const byMarque: Record<string, number> = {};
        const byEnergie: Record<string, number> = {};
        (moteurs || []).forEach((m: any) => {
          if (m.est_disponible !== 1) return;
          const marque = m.marque || "Inconnu";
          const energie = m.energie || "Inconnu";
          byMarque[marque] = (byMarque[marque] || 0) + 1;
          byEnergie[energie] = (byEnergie[energie] || 0) + 1;
        });
        setData({
          topMarques: Object.entries(byMarque).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([name, value]) => ({ name, value })),
          byEnergie: Object.entries(byEnergie).map(([name, value]) => ({ name, value })),
        });
      } else if (tab === "Prix") {
        const { data: moteurs } = await supabase
          .from("v_moteurs_dispo")
          .select("code_moteur, prix_achat_moteur")
          .not("prix_achat_moteur", "is", null)
          .limit(2000);

        // Price ranges
        const ranges = [
          { label: "0–200€", min: 0, max: 200, count: 0 },
          { label: "200–400€", min: 200, max: 400, count: 0 },
          { label: "400–600€", min: 400, max: 600, count: 0 },
          { label: "600–1000€", min: 600, max: 1000, count: 0 },
          { label: "1000€+", min: 1000, max: Infinity, count: 0 },
        ];
        (moteurs || []).forEach((m: any) => {
          const p = m.prix_achat_moteur || 0;
          const range = ranges.find((r) => p >= r.min && p < r.max);
          if (range) range.count++;
        });
        const avg = (moteurs || []).reduce((s: number, m: any) => s + (m.prix_achat_moteur || 0), 0) / ((moteurs || []).length || 1);
        setData({ ranges, avg: Math.round(avg) });
      } else if (tab === "Tendances") {
        const cutoff = new Date();
        cutoff.setMonth(cutoff.getMonth() - 12);
        const [{ data: recData }, { data: expData }] = await Promise.all([
          supabase.from("v_receptions").select("date_reception, nb_moteurs").gte("date_reception", cutoff.toISOString()),
          supabase.from("tbl_expeditions_moteurs").select("date_validation, prix_vente_moteur").gte("date_validation", cutoff.toISOString()),
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
        setData({ months: Object.values(byMonth).sort((a, b) => a.mois.localeCompare(b.mois)) });
      } else {
        // Offres: top selling codes
        const { data: topSales } = await supabase
          .from("tbl_expeditions_moteurs")
          .select("code_moteur, prix_vente_moteur")
          .not("code_moteur", "is", null)
          .limit(2000);
        const codeMap: Record<string, { ventes: number; ca: number }> = {};
        (topSales || []).forEach((e: any) => {
          const k = (e.code_moteur || "").substring(0, 4).toUpperCase();
          if (!k) return;
          if (!codeMap[k]) codeMap[k] = { ventes: 0, ca: 0 };
          codeMap[k].ventes++;
          codeMap[k].ca += e.prix_vente_moteur || 0;
        });
        setData({
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
      <PageHeader title="Analyse avancée" icon="📊" description="Statistiques détaillées du stock et des ventes" />

      <div className="flex bg-white rounded-lg shadow-sm border overflow-hidden mb-6 w-fit">
        {(["Stock", "Prix", "Tendances", "Offres"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-5 py-2 text-sm font-medium transition ${tab === t ? "bg-[#C41E3A] text-white" : "text-gray-600 hover:bg-gray-50"}`}
          >
            {t}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400">Chargement...</div>
      ) : tab === "Stock" && data ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-4">Stock disponible par marque (Top 10)</h3>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.topMarques} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" width={80} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" fill="#C41E3A" radius={[0, 4, 4, 0]} name="Disponibles" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-4">Répartition par énergie</h3>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={data.byEnergie} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {data.byEnergie.map((_: any, i: number) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : tab === "Prix" && data ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-4">Distribution des prix d&apos;achat</h3>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.ranges}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#C41E3A" radius={[6, 6, 0, 0]} name="Nb moteurs" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-sm flex flex-col justify-center items-center">
            <p className="text-gray-500 text-sm mb-2">Prix d&apos;achat moyen</p>
            <p className="text-5xl font-bold text-[#C41E3A]">{data.avg.toLocaleString("fr-FR")} €</p>
          </div>
        </div>
      ) : tab === "Tendances" && data ? (
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h3 className="font-semibold text-gray-700 mb-4">Réceptions vs Ventes — 12 derniers mois</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.months}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="mois" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="recus" fill="#2563EB" radius={[4, 4, 0, 0]} name="Reçus" />
              <Bar dataKey="vendus" fill="#C41E3A" radius={[4, 4, 0, 0]} name="Vendus" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : tab === "Offres" && data ? (
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h3 className="font-semibold text-gray-700 mb-4">Top 15 références les plus vendues</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.topOffres}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="code" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(value, name) => [name === "ca" ? `${Number(value).toLocaleString("fr-FR")} €` : value, name === "ca" ? "CA" : "Ventes"]} />
              <Legend />
              <Bar dataKey="ventes" fill="#C41E3A" radius={[4, 4, 0, 0]} name="Ventes" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : null}
    </div>
  );
}
