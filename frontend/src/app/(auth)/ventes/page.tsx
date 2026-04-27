"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function VentesPage() {
  const [piece, setPiece] = useState<"moteurs" | "boites">("moteurs");
  const [nMonths, setNMonths] = useState(6);
  const [ventesParMois, setVentesParMois] = useState<any[]>([]);
  const [topCodes, setTopCodes] = useState<any[]>([]);
  const [totalVentes, setTotalVentes] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);

      // 3 RPCs qui agrègent côté serveur — ultra rapide
      const [monthsRes, topRes, totalRes] = await Promise.all([
        supabase.rpc("get_ventes_par_mois", { p_piece: piece, p_months: nMonths }),
        piece === "moteurs"
          ? supabase.rpc("get_top_types_vendus", { p_months: nMonths, p_limit: 15 })
          : Promise.resolve({ data: [] as any[] }),
        supabase.rpc("get_ventes_total_count", { p_piece: piece, p_months: nMonths }),
      ]);

      setVentesParMois((monthsRes.data as any[]) || []);
      setTopCodes((topRes.data as any[]) || []);
      setTotalVentes(Number(totalRes.data ?? 0));
      setLoading(false);
    }
    load();
  }, [piece, nMonths]);

  return (
    <div>
      <PageHeader title="Analyse des ventes" description="Tendances et statistiques commerciales" />

      <div className="flex flex-wrap items-center gap-4 mb-6">
        <div className="flex bg-surface-alt rounded-lg border border-border overflow-hidden">
          {(["moteurs", "boites"] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPiece(p)}
              className={`px-4 py-2 text-sm font-medium transition-all ${piece === p ? "bg-brand text-white" : "text-text-dim hover:bg-surface-hover"}`}
            >
              {p === "moteurs" ? "Moteurs" : "Boîtes"}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-text-dim">Période :</span>
          <select
            value={nMonths}
            onChange={(e) => setNMonths(Number(e.target.value))}
            className="border border-border rounded-lg px-3 py-2 text-sm bg-surface-alt text-foreground"
          >
            <option value={3}>3 mois</option>
            <option value={6}>6 mois</option>
            <option value={12}>12 mois</option>
            <option value={24}>24 mois</option>
          </select>
        </div>
        {!loading && (
          <Card className="ml-auto">
            <CardContent className="px-6 py-3 flex items-center gap-3">
              <span className="text-xs text-text-dim uppercase font-semibold">Total ventes</span>
              <span className="text-2xl font-bold text-brand">{totalVentes}</span>
            </CardContent>
          </Card>
        )}
      </div>

      {loading ? (
        <div className="text-center py-16 text-text-muted">Chargement des données...</div>
      ) : ventesParMois.length === 0 ? (
        <div className="text-center py-16 text-text-muted">Aucune vente sur la période sélectionnée</div>
      ) : (
        <>
          <div className="bg-surface border border-border rounded-[14px] p-6 mb-6">
            <h3 className="font-semibold text-foreground mb-4">
              Ventes par mois — {nMonths} derniers mois
            </h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={ventesParMois}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="mois" tick={{ fontSize: 12, fill: "#4B5563" }} />
                <YAxis tick={{ fontSize: 12, fill: "#4B5563" }} />
                <Tooltip contentStyle={{ background: "#FFFFFF", border: "1px solid #E5E7EB", borderRadius: 10, color: "#111827", boxShadow: "0 4px 12px rgba(0,0,0,0.08)" }} />
                <Line
                  type="monotone"
                  dataKey="nb_vendus"
                  stroke="#C41E3A"
                  strokeWidth={3}
                  dot={{ r: 4, fill: "#C41E3A" }}
                  name="Ventes"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {topCodes.length > 0 && (
            <div className="bg-surface border border-border rounded-[14px] p-6">
              <h3 className="font-semibold text-foreground mb-4">Top 15 types moteur vendus</h3>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={topCodes}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="type_moteur" tick={{ fontSize: 11, fill: "#4B5563" }} />
                  <YAxis tick={{ fontSize: 12, fill: "#4B5563" }} />
                  <Tooltip contentStyle={{ background: "#FFFFFF", border: "1px solid #E5E7EB", borderRadius: 10, color: "#111827", boxShadow: "0 4px 12px rgba(0,0,0,0.08)" }} />
                  <Bar dataKey="nb_vendus" fill="#C41E3A" radius={[6, 6, 0, 0]} name="Ventes" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
}
