"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type Piece = {
  n_piece: number;
  reference?: string;
  designation?: string;
  marque?: string;
  quantite_stock?: number;
  quantite_min?: number;
  prix_achat?: number;
  prix_vente?: number;
  emplacement?: string;
};

export default function PiecesPage() {
  const [search, setSearch] = useState("");
  const [alerte, setAlerte] = useState(false);
  const [pieces, setPieces] = useState<Piece[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      let query = supabase
        .from("tbl_pieces_detachees")
        .select("n_piece, reference, designation, marque, quantite_stock, quantite_min, prix_achat, prix_vente, emplacement")
        .order("designation", { ascending: true })
        .limit(500);

      if (search) {
        query = query.or(`reference.ilike.%${search}%,designation.ilike.%${search}%`);
      }
      if (alerte) {
        query = query.lt("quantite_stock", "quantite_min");
      }

      const { data } = await query;
      setPieces(data || []);
      setLoading(false);
    }
    load();
  }, [search, alerte]);

  const nbAlertes = pieces.filter((p) => (p.quantite_stock || 0) < (p.quantite_min || 0)).length;
  const valeurStock = pieces.reduce((s, p) => s + (p.quantite_stock || 0) * (p.prix_achat || 0), 0);

  return (
    <div>
      <PageHeader title="Pièces détachées" icon="🔩" description="Gestion du stock pièces (alternateurs, démarreurs...)" />

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-gray-500 font-semibold uppercase">Références</p>
            <p className="text-2xl font-bold text-[#C41E3A]">{pieces.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-gray-500 font-semibold uppercase">Alertes stock</p>
            <p className="text-2xl font-bold text-amber-600">{nbAlertes}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-gray-500 font-semibold uppercase">Valeur stock</p>
            <p className="text-2xl font-bold text-gray-700">{Math.round(valeurStock).toLocaleString("fr-FR")} €</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-5">
        <Input
          placeholder="Rechercher (référence, désignation...)"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={alerte}
            onChange={(e) => setAlerte(e.target.checked)}
            className="rounded border-gray-300"
          />
          <span className="text-sm text-amber-700 font-medium">Alertes seulement</span>
        </label>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Chargement...</div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Référence</th>
                  <th className="px-4 py-3 text-left">Désignation</th>
                  <th className="px-4 py-3 text-left">Marque</th>
                  <th className="px-4 py-3 text-center">Stock</th>
                  <th className="px-4 py-3 text-center">Min</th>
                  <th className="px-4 py-3 text-right">Prix achat</th>
                  <th className="px-4 py-3 text-right">Prix vente</th>
                  <th className="px-4 py-3 text-left">Emplacement</th>
                  <th className="px-4 py-3 text-center">Alerte</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {pieces.map((p) => {
                  const isAlerte = (p.quantite_stock || 0) < (p.quantite_min || 0);
                  return (
                    <tr key={p.n_piece} className={`hover:bg-gray-50 ${isAlerte ? "bg-amber-50" : ""}`}>
                      <td className="px-4 py-3 font-mono text-xs">{p.reference || "—"}</td>
                      <td className="px-4 py-3 font-medium">{p.designation || "—"}</td>
                      <td className="px-4 py-3 text-gray-600">{p.marque || "—"}</td>
                      <td className="px-4 py-3 text-center font-semibold tabular-nums">{p.quantite_stock ?? 0}</td>
                      <td className="px-4 py-3 text-center text-gray-400 tabular-nums">{p.quantite_min ?? 0}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{p.prix_achat ? `${p.prix_achat.toLocaleString("fr-FR")} €` : "—"}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{p.prix_vente ? `${p.prix_vente.toLocaleString("fr-FR")} €` : "—"}</td>
                      <td className="px-4 py-3 text-gray-600 text-xs">{p.emplacement || "—"}</td>
                      <td className="px-4 py-3 text-center">
                        {isAlerte && (
                          <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100">Stock bas</Badge>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {pieces.length === 0 && (
            <p className="text-center py-10 text-gray-400">Aucune pièce trouvée</p>
          )}
        </div>
      )}
    </div>
  );
}
