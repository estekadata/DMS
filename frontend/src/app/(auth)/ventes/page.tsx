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
      const table = piece === "moteurs" ? "tbl_expeditions_moteurs" : "tbl_expeditions_boites";
      const cutoff = new Date();
      cutoff.setMonth(cutoff.getMonth() - nMonths);

      const selectCols = piece === "moteurs"
        ? "date_validation, prix_vente_moteur, n_moteur"
        : "date_validation, n_bv";

      const { data } = await supabase
        .from(table)
        .select(selectCols)
        .gte("date_validation", cutoff.toISOString())
        .order("date_validation", { ascending: true });

      if (!data) { setLoading(false); return; }

      setTotalVentes(data.length);

      const byMonth: Record<string, number> = {};
      data.forEach((row: any) => {
        const d = new Date(row.date_validation);
        const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
        byMonth[key] = (byMonth[key] || 0) + 1;
      });
      setVentesParMois(
        Object.entries(byMonth).map(([mois, nb_vendus]) => ({ mois, nb_vendus }))
      );

      if (piece === "moteurs") {
        const motorIds = [...new Set(data.map((r: any) => r.n_moteur).filter(Boolean))].slice(0, 2000);
        if (motorIds.length > 0) {
          const { data: motors } = await supabase
            .from("tbl_moteurs")
            .select("n_moteur, code_moteur")
            .in("n_moteur", motorIds);

          const codeCount: Record<string, number> = {};
          (motors || []).forEach((m: any) => {
            const code = (m.code_moteur || "").substring(0, 3).toUpperCase();
            if (code) codeCount[code] = (codeCount[code] || 0) + 1;
          });
          setTopCodes(
            Object.entries(codeCount)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 15)
              .map(([type_moteur, nb_vendus]) => ({ type_moteur, nb_vendus }))
          );
        }
      } else {
        setTopCodes([]);
      }
      setLoading(false);
    }
    load();
  }, [piece, nMonths]);

  return (
    <div>
      <PageHeader title="Analyse des ventes" icon="📈" description="Tendances et statistiques commerciales" />

      <div className="flex flex-wrap items-center gap-4 mb-6">
        <div className="flex bg-white rounded-lg shadow-sm border overflow-hidden">
          {(["moteurs", "boites"] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPiece(p)}
              className={`px-4 py-2 text-sm font-medium transition ${piece === p ? "bg-[#C41E3A] text-white" : "text-gray-600 hover:bg-gray-50"}`}
            >
              {p === "moteurs" ? "Moteurs" : "Boîtes"}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Période :</span>
          <select
            value={nMonths}
            onChange={(e) => setNMonths(Number(e.target.value))}
            className="border rounded-lg px-3 py-2 text-sm bg-white"
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
              <span className="text-xs text-gray-500 uppercase font-semibold">Total ventes</span>
              <span className="text-2xl font-bold text-[#C41E3A]">{totalVentes}</span>
            </CardContent>
          </Card>
        )}
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400">Chargement des données...</div>
      ) : ventesParMois.length === 0 ? (
        <div className="text-center py-16 text-gray-400">Aucune vente sur la période sélectionnée</div>
      ) : (
        <>
          <div className="bg-white rounded-2xl p-6 shadow-sm mb-6">
            <h3 className="font-semibold text-gray-700 mb-4">
              Ventes par mois — {nMonths} derniers mois
            </h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={ventesParMois}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="mois" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
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
            <div className="bg-white rounded-2xl p-6 shadow-sm">
              <h3 className="font-semibold text-gray-700 mb-4">Top 15 types moteur vendus</h3>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={topCodes}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="type_moteur" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="nb_vendus" fill="#8B1A2B" radius={[6, 6, 0, 0]} name="Ventes" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
}
