"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function BoitesPage() {
  const [search, setSearch] = useState("");
  const [statut, setStatut] = useState("Tous");
  const [boites, setBoites] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  async function loadBoites() {
    setLoading(true);
    let query = supabase
      .from("v_boites_dispo")
      .select("n_bv, code_bv, num_serie, marque, energie, prix_achat_bv, est_disponible, archiver")
      .order("n_bv", { ascending: false })
      .limit(500);

    if (search) {
      query = query.or(`code_bv.ilike.%${search}%,num_serie.ilike.%${search}%`);
    }
    if (statut === "Disponible") query = query.eq("est_disponible", 1);
    if (statut === "Vendu/Archivé") query = query.eq("archiver", 1);

    const { data } = await query;
    setBoites(data || []);
    setLoading(false);
  }

  useEffect(() => { loadBoites(); }, [search, statut]);

  const nbDispo = boites.filter((b) => b.est_disponible === 1).length;
  const nbReserve = boites.filter((b) => b.est_disponible === 0 && !b.archiver).length;
  const nbArchive = boites.filter((b) => b.archiver).length;

  return (
    <div>
      <PageHeader title="Identification Boîtes de vitesse" icon="⚙️" description="Recherche et consultation du stock BV" />

      <div className="flex flex-wrap gap-3 mb-6">
        <Input
          placeholder="Rechercher (code BV, num série...)"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
        <select
          value={statut}
          onChange={(e) => setStatut(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm bg-white"
        >
          <option>Tous</option>
          <option>Disponible</option>
          <option>Réservé</option>
          <option>Vendu/Archivé</option>
        </select>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card><CardContent className="p-4"><p className="text-xs text-gray-500 font-semibold uppercase">Résultats</p><p className="text-2xl font-bold text-[#C41E3A]">{boites.length}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-gray-500 font-semibold uppercase">Disponibles</p><p className="text-2xl font-bold text-emerald-600">{nbDispo}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-gray-500 font-semibold uppercase">Réservées</p><p className="text-2xl font-bold text-amber-600">{nbReserve}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-gray-500 font-semibold uppercase">Archivées</p><p className="text-2xl font-bold text-gray-500">{nbArchive}</p></CardContent></Card>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Chargement...</div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">N°</th>
                  <th className="px-4 py-3 text-left">Code BV</th>
                  <th className="px-4 py-3 text-left">Num série</th>
                  <th className="px-4 py-3 text-left">Marque</th>
                  <th className="px-4 py-3 text-left">Énergie</th>
                  <th className="px-4 py-3 text-right">Prix achat</th>
                  <th className="px-4 py-3 text-center">Statut</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {boites.map((b) => (
                  <tr key={b.n_bv} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-gray-400">{b.n_bv}</td>
                    <td className="px-4 py-3 font-semibold text-gray-900">{b.code_bv || "—"}</td>
                    <td className="px-4 py-3 text-gray-600">{b.num_serie || "—"}</td>
                    <td className="px-4 py-3">{b.marque || "—"}</td>
                    <td className="px-4 py-3">{b.energie || "—"}</td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {b.prix_achat_bv ? `${Math.round(b.prix_achat_bv).toLocaleString("fr-FR")} €` : "—"}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {b.archiver ? (
                        <Badge className="bg-gray-100 text-gray-600 hover:bg-gray-100">Archivée</Badge>
                      ) : b.est_disponible === 1 ? (
                        <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100">Disponible</Badge>
                      ) : (
                        <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100">Réservée</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {boites.length === 0 && (
            <p className="text-center py-10 text-gray-400">Aucune boîte trouvée</p>
          )}
        </div>
      )}
    </div>
  );
}
