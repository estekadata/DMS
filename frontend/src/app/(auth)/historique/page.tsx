"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type Tab = "Réceptions" | "Expéditions" | "Stats";

type Reception = { n_reception: number; date_reception: string; fournisseur?: string; nb_moteurs?: number; montant_total?: number; };
type Expedition = { n_expedition: number; date_validation: string; client?: string; code_moteur?: string; prix_vente_moteur?: number; };
type Stats = { mois: string; recus: number; vendus: number; };

export default function HistoriquePage() {
  const [tab, setTab] = useState<Tab>("Réceptions");
  const [receptions, setReceptions] = useState<Reception[]>([]);
  const [expeditions, setExpeditions] = useState<Expedition[]>([]);
  const [stats, setStats] = useState<Stats[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      if (tab === "Réceptions") {
        const { data } = await supabase
          .from("v_receptions")
          .select("n_reception, date_reception, fournisseur, nb_moteurs, montant_total")
          .order("date_reception", { ascending: false })
          .limit(200);
        setReceptions(data || []);
      } else if (tab === "Expéditions") {
        const { data } = await supabase
          .from("tbl_expeditions_moteurs")
          .select("n_expedition, date_validation, client, code_moteur, prix_vente_moteur")
          .order("date_validation", { ascending: false })
          .limit(200);
        setExpeditions(data || []);
      } else {
        // Stats: build from expeditions grouped by month
        const cutoff = new Date();
        cutoff.setMonth(cutoff.getMonth() - 12);
        const [{ data: recData }, { data: expData }] = await Promise.all([
          supabase.from("v_receptions").select("date_reception, nb_moteurs").gte("date_reception", cutoff.toISOString()),
          supabase.from("tbl_expeditions_moteurs").select("date_validation").gte("date_validation", cutoff.toISOString()),
        ]);
        const byMonth: Record<string, { recus: number; vendus: number }> = {};
        (recData || []).forEach((r: any) => {
          const k = r.date_reception?.substring(0, 7) || "";
          if (!byMonth[k]) byMonth[k] = { recus: 0, vendus: 0 };
          byMonth[k].recus += r.nb_moteurs || 0;
        });
        (expData || []).forEach((e: any) => {
          const k = e.date_validation?.substring(0, 7) || "";
          if (!byMonth[k]) byMonth[k] = { recus: 0, vendus: 0 };
          byMonth[k].vendus++;
        });
        setStats(
          Object.entries(byMonth)
            .sort((a, b) => a[0].localeCompare(b[0]))
            .map(([mois, v]) => ({ mois, ...v }))
        );
      }
      setLoading(false);
    }
    load();
  }, [tab]);

  return (
    <div>
      <PageHeader title="Historique" icon="📜" description="Réceptions, expéditions et statistiques" />

      <div className="flex bg-white rounded-lg shadow-sm border overflow-hidden mb-6 w-fit">
        {(["Réceptions", "Expéditions", "Stats"] as Tab[]).map((t) => (
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
        <div className="text-center py-12 text-gray-400">Chargement...</div>
      ) : tab === "Réceptions" ? (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
              <tr>
                <th className="px-4 py-3 text-left">N°</th>
                <th className="px-4 py-3 text-left">Date</th>
                <th className="px-4 py-3 text-left">Fournisseur</th>
                <th className="px-4 py-3 text-center">Moteurs</th>
                <th className="px-4 py-3 text-right">Montant</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {receptions.map((r) => (
                <tr key={r.n_reception} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs text-gray-400">{r.n_reception}</td>
                  <td className="px-4 py-3">{r.date_reception ? new Date(r.date_reception).toLocaleDateString("fr-FR") : "—"}</td>
                  <td className="px-4 py-3 font-medium">{r.fournisseur || "—"}</td>
                  <td className="px-4 py-3 text-center">{r.nb_moteurs ?? "—"}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{r.montant_total ? `${Math.round(r.montant_total).toLocaleString("fr-FR")} €` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {receptions.length === 0 && <p className="text-center py-10 text-gray-400">Aucune réception</p>}
        </div>
      ) : tab === "Expéditions" ? (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
              <tr>
                <th className="px-4 py-3 text-left">N°</th>
                <th className="px-4 py-3 text-left">Date</th>
                <th className="px-4 py-3 text-left">Client</th>
                <th className="px-4 py-3 text-left">Code moteur</th>
                <th className="px-4 py-3 text-right">Prix vente</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {expeditions.map((e) => (
                <tr key={e.n_expedition} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs text-gray-400">{e.n_expedition}</td>
                  <td className="px-4 py-3">{e.date_validation ? new Date(e.date_validation).toLocaleDateString("fr-FR") : "—"}</td>
                  <td className="px-4 py-3 font-medium">{e.client || "—"}</td>
                  <td className="px-4 py-3">{e.code_moteur || "—"}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{e.prix_vente_moteur ? `${Math.round(e.prix_vente_moteur).toLocaleString("fr-FR")} €` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {expeditions.length === 0 && <p className="text-center py-10 text-gray-400">Aucune expédition</p>}
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
              <tr>
                <th className="px-4 py-3 text-left">Mois</th>
                <th className="px-4 py-3 text-center">Moteurs reçus</th>
                <th className="px-4 py-3 text-center">Moteurs vendus</th>
                <th className="px-4 py-3 text-center">Solde</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {stats.map((s) => (
                <tr key={s.mois} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-semibold">{s.mois}</td>
                  <td className="px-4 py-3 text-center tabular-nums">{s.recus}</td>
                  <td className="px-4 py-3 text-center tabular-nums">{s.vendus}</td>
                  <td className="px-4 py-3 text-center">
                    <Badge
                      className={
                        s.recus - s.vendus >= 0
                          ? "bg-blue-100 text-blue-700 hover:bg-blue-100"
                          : "bg-red-100 text-red-700 hover:bg-red-100"
                      }
                    >
                      {s.recus - s.vendus >= 0 ? "+" : ""}{s.recus - s.vendus}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {stats.length === 0 && <p className="text-center py-10 text-gray-400">Aucune donnée</p>}
        </div>
      )}
    </div>
  );
}
