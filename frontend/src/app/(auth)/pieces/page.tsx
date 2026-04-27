"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const ROW_LIMIT = 1000;
const STOCK_BAS = 2; // seuil d'alerte stock bas

type Piece = {
  id: number;
  categorie: string;
  marque: string;
  reference: string;
  modele: string;
  stock: number;
};

export default function PiecesPage() {
  const [search, setSearch] = useState("");
  const [categorie, setCategorie] = useState("Toutes");
  const [alerte, setAlerte] = useState(false);
  const [pieces, setPieces] = useState<Piece[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [counts, setCounts] = useState({ total: 0, alertes: 0, stockTotal: 0 });
  const [loading, setLoading] = useState(true);

  function applyFilters<T extends { or: (f: string) => T; eq: (c: string, v: any) => T; lte: (c: string, v: any) => T }>(q: T): T {
    let out = q;
    if (search) out = out.or(`reference.ilike.%${search}%,modele.ilike.%${search}%,marque.ilike.%${search}%`);
    if (categorie !== "Toutes") out = out.eq("categorie", categorie);
    if (alerte) out = out.lte("stock", STOCK_BAS);
    return out;
  }

  useEffect(() => {
    async function loadCategories() {
      const { data } = await supabase
        .from("tbl_pieces_detachees")
        .select("categorie")
        .limit(5000);
      const uniq = [...new Set((data || []).map((r: any) => r.categorie).filter(Boolean))].sort();
      setCategories(uniq as string[]);
    }
    loadCategories();
  }, []);

  useEffect(() => {
    async function load() {
      setLoading(true);

      let rowsQ = supabase
        .from("tbl_pieces_detachees")
        .select("id, categorie, marque, reference, modele, stock")
        .order("reference", { ascending: true })
        .limit(ROW_LIMIT);
      rowsQ = applyFilters(rowsQ as any) as any;

      const countBase = () => applyFilters(
        supabase.from("tbl_pieces_detachees").select("*", { count: "exact", head: true }) as any
      );
      const totalBase = () => {
        let q = supabase.from("tbl_pieces_detachees").select("*", { count: "exact", head: true }) as any;
        if (search) q = q.or(`reference.ilike.%${search}%,modele.ilike.%${search}%,marque.ilike.%${search}%`);
        if (categorie !== "Toutes") q = q.eq("categorie", categorie);
        return q;
      };

      const [rowsRes, totalRes, alertRes] = await Promise.all([
        rowsQ,
        totalBase(),
        totalBase().lte("stock", STOCK_BAS),
      ]);

      const rows = (rowsRes.data || []) as Piece[];
      setPieces(rows);
      setCounts({
        total: totalRes.count || 0,
        alertes: alertRes.count || 0,
        stockTotal: rows.reduce((s, p) => s + (p.stock || 0), 0),
      });
      setLoading(false);
    }
    load();
  }, [search, categorie, alerte]);

  return (
    <div>
      <PageHeader title="Pièces détachées" description="Gestion du stock pièces (alternateurs, démarreurs...)" />

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card><CardContent className="p-4"><p className="text-xs text-text-dim font-semibold uppercase">Références</p><p className="text-2xl font-bold text-brand">{counts.total.toLocaleString("fr-FR")}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-text-dim font-semibold uppercase">Stock bas (≤ {STOCK_BAS})</p><p className="text-2xl font-bold text-amber-600">{counts.alertes.toLocaleString("fr-FR")}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-text-dim font-semibold uppercase">Unités affichées</p><p className="text-2xl font-bold text-foreground">{counts.stockTotal.toLocaleString("fr-FR")}</p></CardContent></Card>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-5">
        <Input
          placeholder="Rechercher (référence, modèle, marque...)"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm bg-surface-alt border-border text-foreground placeholder:text-text-muted"
        />
        <select
          value={categorie}
          onChange={(e) => setCategorie(e.target.value)}
          className="border border-border rounded-lg px-3 py-2 text-sm bg-surface-alt text-foreground"
        >
          <option>Toutes</option>
          {categories.map((c) => <option key={c}>{c}</option>)}
        </select>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={alerte}
            onChange={(e) => setAlerte(e.target.checked)}
            className="rounded border-border bg-surface-alt"
          />
          <span className="text-sm text-amber-600 font-medium">Stock bas seulement</span>
        </label>
      </div>

      {counts.total > pieces.length && !loading && (
        <p className="text-xs text-text-muted mb-3">Affichage de {pieces.length.toLocaleString("fr-FR")} pièces sur {counts.total.toLocaleString("fr-FR")} — affinez via la recherche.</p>
      )}

      {loading ? (
        <div className="text-center py-12 text-text-muted">Chargement...</div>
      ) : (
        <div className="bg-surface border border-border rounded-[14px] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-surface-alt text-text-dim text-xs uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Catégorie</th>
                  <th className="px-4 py-3 text-left">Référence</th>
                  <th className="px-4 py-3 text-left">Modèle</th>
                  <th className="px-4 py-3 text-left">Marque</th>
                  <th className="px-4 py-3 text-center">Stock</th>
                  <th className="px-4 py-3 text-center">Alerte</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {pieces.map((p) => {
                  const isAlerte = (p.stock || 0) <= STOCK_BAS;
                  return (
                    <tr key={p.id} className={`hover:bg-surface-hover transition-colors ${isAlerte ? "bg-[rgba(251,191,36,0.05)]" : ""}`}>
                      <td className="px-4 py-3 text-text-dim text-xs">{p.categorie || "—"}</td>
                      <td className="px-4 py-3 font-mono text-xs text-foreground font-semibold">{p.reference || "—"}</td>
                      <td className="px-4 py-3 text-text-dim">{p.modele || "—"}</td>
                      <td className="px-4 py-3 text-text-dim">{p.marque || "—"}</td>
                      <td className="px-4 py-3 text-center font-semibold tabular-nums text-foreground">{p.stock ?? 0}</td>
                      <td className="px-4 py-3 text-center">
                        {isAlerte && (
                          <Badge className="bg-[rgba(251,191,36,0.10)] text-amber-600 border border-[rgba(251,191,36,0.20)] hover:bg-[rgba(251,191,36,0.15)]">Stock bas</Badge>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {pieces.length === 0 && (
            <p className="text-center py-10 text-text-muted italic">Aucune pièce trouvée</p>
          )}
        </div>
      )}
    </div>
  );
}
