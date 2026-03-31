"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

type Centre = {
  n_centre: number;
  nom?: string;
  ville?: string;
  departement?: string;
  contact?: string;
  telephone?: string;
  email?: string;
  actif?: boolean;
  nb_commandes?: number;
};

export default function VhuPage() {
  const [centres, setCentres] = useState<Centre[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Centre | null>(null);
  const [commandes, setCommandes] = useState<any[]>([]);

  useEffect(() => {
    async function load() {
      setLoading(true);
      let query = supabase
        .from("tbl_centres_vhu")
        .select("n_centre, nom, ville, departement, contact, telephone, email, actif, nb_commandes")
        .order("nom", { ascending: true })
        .limit(200);

      if (search) query = query.or(`nom.ilike.%${search}%,ville.ilike.%${search}%`);

      const { data } = await query;
      setCentres(data || []);
      setLoading(false);
    }
    load();
  }, [search]);

  async function openCentre(centre: Centre) {
    setSelected(centre);
    const { data } = await supabase
      .from("v_commandes_vhu")
      .select("n_commande, date_commande, code_moteur, statut, prix")
      .eq("n_centre", centre.n_centre)
      .order("date_commande", { ascending: false })
      .limit(50);
    setCommandes(data || []);
  }

  const nbActifs = centres.filter((c) => c.actif !== false).length;

  return (
    <div>
      <PageHeader title="Centres VHU" icon="🛠️" description="Interface de gestion des centres Véhicules Hors d'Usage" />

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-gray-500 font-semibold uppercase">Centres actifs</p>
            <p className="text-2xl font-bold text-[#C41E3A]">{nbActifs}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-gray-500 font-semibold uppercase">Total centres</p>
            <p className="text-2xl font-bold text-gray-700">{centres.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-gray-500 font-semibold uppercase">Commandes actives</p>
            <p className="text-2xl font-bold text-amber-600">—</p>
          </CardContent>
        </Card>
      </div>

      <Input
        placeholder="Rechercher par nom ou ville..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-sm mb-5"
      />

      <div className={`grid gap-6 ${selected ? "grid-cols-2" : "grid-cols-1"}`}>
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          {loading ? (
            <p className="text-center py-10 text-gray-400">Chargement...</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Nom</th>
                  <th className="px-4 py-3 text-left">Ville</th>
                  <th className="px-4 py-3 text-left">Dept</th>
                  <th className="px-4 py-3 text-left">Contact</th>
                  <th className="px-4 py-3 text-left">Téléphone</th>
                  <th className="px-4 py-3 text-center">Statut</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {centres.map((c) => (
                  <tr
                    key={c.n_centre}
                    onClick={() => openCentre(c)}
                    className={`hover:bg-gray-50 cursor-pointer ${selected?.n_centre === c.n_centre ? "bg-red-50" : ""}`}
                  >
                    <td className="px-4 py-3 font-semibold">{c.nom || "—"}</td>
                    <td className="px-4 py-3 text-gray-600">{c.ville || "—"}</td>
                    <td className="px-4 py-3 text-gray-600">{c.departement || "—"}</td>
                    <td className="px-4 py-3">{c.contact || "—"}</td>
                    <td className="px-4 py-3 font-mono text-xs">{c.telephone || "—"}</td>
                    <td className="px-4 py-3 text-center">
                      <Badge
                        className={
                          c.actif !== false
                            ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-100"
                            : "bg-gray-100 text-gray-500 hover:bg-gray-100"
                        }
                      >
                        {c.actif !== false ? "Actif" : "Inactif"}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {!loading && centres.length === 0 && (
            <p className="text-center py-10 text-gray-400">Aucun centre trouvé</p>
          )}
        </div>

        {selected && (
          <div className="bg-white rounded-xl shadow-sm p-5">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="font-bold text-gray-900">{selected.nom}</h3>
                <p className="text-sm text-gray-500">{selected.ville} — {selected.email || selected.telephone || ""}</p>
              </div>
              <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-600 text-lg">✕</button>
            </div>
            <h4 className="text-sm font-semibold text-gray-600 mb-3">Dernières commandes</h4>
            {commandes.length === 0 ? (
              <p className="text-sm text-gray-400">Aucune commande enregistrée</p>
            ) : (
              <table className="w-full text-sm">
                <thead className="text-xs text-gray-500 uppercase bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left">Date</th>
                    <th className="px-3 py-2 text-left">Code moteur</th>
                    <th className="px-3 py-2 text-right">Prix</th>
                    <th className="px-3 py-2 text-center">Statut</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {commandes.map((cmd) => (
                    <tr key={cmd.n_commande} className="hover:bg-gray-50">
                      <td className="px-3 py-2 text-gray-600">{cmd.date_commande ? new Date(cmd.date_commande).toLocaleDateString("fr-FR") : "—"}</td>
                      <td className="px-3 py-2 font-medium">{cmd.code_moteur || "—"}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{cmd.prix ? `${Math.round(cmd.prix)} €` : "—"}</td>
                      <td className="px-3 py-2 text-center">
                        <Badge className="bg-gray-100 text-gray-600 hover:bg-gray-100 text-xs">{cmd.statut || "—"}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
