"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function MoteursPage() {
  const [search, setSearch] = useState("");
  const [statut, setStatut] = useState("Tous");
  const [moteurs, setMoteurs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  async function loadMoteurs() {
    setLoading(true);
    let query = supabase
      .from("v_moteurs_dispo")
      .select("n_moteur, code_moteur, num_serie, marque, energie, prix_achat_moteur, est_disponible, archiver")
      .order("n_moteur", { ascending: false })
      .limit(500);

    if (search) {
      query = query.or(`code_moteur.ilike.%${search}%,num_serie.ilike.%${search}%`);
    }
    if (statut === "Disponible") query = query.eq("est_disponible", 1);
    if (statut === "Vendu/Archivé") query = query.eq("archiver", 1);

    const { data } = await query;
    setMoteurs(data || []);
    setLoading(false);
  }

  useEffect(() => { loadMoteurs(); }, [search, statut]);

  const nbDispo = moteurs.filter((m) => m.est_disponible === 1).length;
  const nbReserve = moteurs.filter((m) => m.est_disponible === 0 && !m.archiver).length;
  const nbArchive = moteurs.filter((m) => m.archiver).length;

  return (
    <div>
      <PageHeader title="Identification Moteurs" icon="🔍" description="Recherche et consultation du stock moteurs" />

      <div className="flex flex-wrap gap-3 mb-6">
        <Input
          placeholder="Rechercher (code moteur, num série...)"
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
        <Card><CardContent className="p-4"><p className="text-xs text-gray-500 font-semibold uppercase">Résultats</p><p className="text-2xl font-bold text-[#C41E3A]">{moteurs.length}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-gray-500 font-semibold uppercase">Disponibles</p><p className="text-2xl font-bold text-emerald-600">{nbDispo}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-gray-500 font-semibold uppercase">Réservés</p><p className="text-2xl font-bold text-amber-600">{nbReserve}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-gray-500 font-semibold uppercase">Archivés</p><p className="text-2xl font-bold text-gray-500">{nbArchive}</p></CardContent></Card>
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
                  <th className="px-4 py-3 text-left">Code moteur</th>
                  <th className="px-4 py-3 text-left">Num série</th>
                  <th className="px-4 py-3 text-left">Marque</th>
                  <th className="px-4 py-3 text-left">Énergie</th>
                  <th className="px-4 py-3 text-right">Prix achat</th>
                  <th className="px-4 py-3 text-center">Statut</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {moteurs.map((m) => (
                  <tr key={m.n_moteur} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-gray-400">{m.n_moteur}</td>
                    <td className="px-4 py-3 font-semibold text-gray-900">{m.code_moteur || "—"}</td>
                    <td className="px-4 py-3 text-gray-600">{m.num_serie || "—"}</td>
                    <td className="px-4 py-3">{m.marque || "—"}</td>
                    <td className="px-4 py-3">{m.energie || "—"}</td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {m.prix_achat_moteur ? `${Math.round(m.prix_achat_moteur).toLocaleString("fr-FR")} €` : "—"}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {m.archiver ? (
                        <Badge className="bg-gray-100 text-gray-600 hover:bg-gray-100">Archivé</Badge>
                      ) : m.est_disponible === 1 ? (
                        <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100">Disponible</Badge>
                      ) : (
                        <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100">Réservé</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {moteurs.length === 0 && (
            <p className="text-center py-10 text-gray-400">Aucun moteur trouvé</p>
          )}
        </div>
      )}
    </div>
  );
}
