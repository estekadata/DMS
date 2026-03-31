"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type Reception = {
  n_reception: number;
  date_reception: string;
  fournisseur?: string;
  nb_moteurs?: number;
  nb_boites?: number;
  montant_total?: number;
  statut?: string;
};

type Detail = { n_moteur?: number; code_moteur?: string; num_serie?: string; marque?: string; prix_achat_moteur?: number; };

export default function ReceptionsPage() {
  const [search, setSearch] = useState("");
  const [receptions, setReceptions] = useState<Reception[]>([]);
  const [selected, setSelected] = useState<Reception | null>(null);
  const [details, setDetails] = useState<Detail[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      let query = supabase
        .from("v_receptions")
        .select("n_reception, date_reception, fournisseur, nb_moteurs, nb_boites, montant_total, statut")
        .order("n_reception", { ascending: false })
        .limit(200);

      if (search) query = query.ilike("fournisseur", `%${search}%`);

      const { data } = await query;
      setReceptions(data || []);
      setLoading(false);
    }
    load();
  }, [search]);

  async function openDetail(rec: Reception) {
    setSelected(rec);
    setDetailLoading(true);
    const { data } = await supabase
      .from("tbl_moteurs")
      .select("n_moteur, code_moteur, num_serie, marque, prix_achat_moteur")
      .eq("n_reception", rec.n_reception)
      .limit(100);
    setDetails(data || []);
    setDetailLoading(false);
  }

  const totalMoteurs = receptions.reduce((s, r) => s + (r.nb_moteurs || 0), 0);
  const totalMontant = receptions.reduce((s, r) => s + (r.montant_total || 0), 0);

  return (
    <div>
      <PageHeader title="Réceptions" icon="📥" description="Gestion des arrivages fournisseurs" />

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card><CardContent className="p-4"><p className="text-xs text-gray-500 font-semibold uppercase">Réceptions</p><p className="text-2xl font-bold text-[#C41E3A]">{receptions.length}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-gray-500 font-semibold uppercase">Total moteurs</p><p className="text-2xl font-bold text-gray-700">{totalMoteurs}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-gray-500 font-semibold uppercase">Montant total</p><p className="text-2xl font-bold text-gray-700">{Math.round(totalMontant).toLocaleString("fr-FR")} €</p></CardContent></Card>
      </div>

      <Input
        placeholder="Rechercher par fournisseur..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-sm mb-5"
      />

      <div className={`grid gap-6 ${selected ? "grid-cols-2" : "grid-cols-1"}`}>
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            {loading ? (
              <p className="text-center py-10 text-gray-400">Chargement...</p>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
                  <tr>
                    <th className="px-4 py-3 text-left">N°</th>
                    <th className="px-4 py-3 text-left">Date</th>
                    <th className="px-4 py-3 text-left">Fournisseur</th>
                    <th className="px-4 py-3 text-center">Moteurs</th>
                    <th className="px-4 py-3 text-right">Montant</th>
                    <th className="px-4 py-3 text-center">Statut</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {receptions.map((r) => (
                    <tr
                      key={r.n_reception}
                      onClick={() => openDetail(r)}
                      className={`hover:bg-gray-50 cursor-pointer ${selected?.n_reception === r.n_reception ? "bg-red-50" : ""}`}
                    >
                      <td className="px-4 py-3 font-mono text-xs">{r.n_reception}</td>
                      <td className="px-4 py-3 text-gray-600">{r.date_reception ? new Date(r.date_reception).toLocaleDateString("fr-FR") : "—"}</td>
                      <td className="px-4 py-3 font-medium">{r.fournisseur || "—"}</td>
                      <td className="px-4 py-3 text-center">{r.nb_moteurs ?? "—"}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{r.montant_total ? `${Math.round(r.montant_total).toLocaleString("fr-FR")} €` : "—"}</td>
                      <td className="px-4 py-3 text-center">
                        <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100">{r.statut || "Reçu"}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
          {!loading && receptions.length === 0 && <p className="text-center py-10 text-gray-400">Aucune réception</p>}
        </div>

        {selected && (
          <div className="bg-white rounded-xl shadow-sm p-5">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="font-bold text-gray-900">Réception #{selected.n_reception}</h3>
                <p className="text-sm text-gray-500">{selected.fournisseur} — {selected.date_reception ? new Date(selected.date_reception).toLocaleDateString("fr-FR") : ""}</p>
              </div>
              <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-600 text-lg">✕</button>
            </div>
            {detailLoading ? (
              <p className="text-gray-400 text-sm">Chargement des moteurs...</p>
            ) : (
              <table className="w-full text-sm">
                <thead className="text-xs text-gray-500 uppercase bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left">Code</th>
                    <th className="px-3 py-2 text-left">Num série</th>
                    <th className="px-3 py-2 text-left">Marque</th>
                    <th className="px-3 py-2 text-right">Prix achat</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {details.map((d) => (
                    <tr key={d.n_moteur} className="hover:bg-gray-50">
                      <td className="px-3 py-2 font-semibold">{d.code_moteur || "—"}</td>
                      <td className="px-3 py-2 text-gray-600 text-xs">{d.num_serie || "—"}</td>
                      <td className="px-3 py-2">{d.marque || "—"}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{d.prix_achat_moteur ? `${Math.round(d.prix_achat_moteur)} €` : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {!detailLoading && details.length === 0 && <p className="text-gray-400 text-sm mt-4">Aucun moteur lié à cette réception</p>}
          </div>
        )}
      </div>
    </div>
  );
}
