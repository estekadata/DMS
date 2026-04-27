"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const ROW_LIMIT = 1000;

export default function BoitesPage() {
  const [search, setSearch] = useState("");
  const [statut, setStatut] = useState("Tous");
  const [boites, setBoites] = useState<any[]>([]);
  const [counts, setCounts] = useState({ total: 0, dispo: 0, reserve: 0, vendu: 0 });
  const [loading, setLoading] = useState(false);

  function applySearch<T extends { or: (f: string) => T }>(q: T): T {
    return search
      ? q.or(`ref_bv.ilike.%${search}%,num_interne_bv.ilike.%${search}%,num_interne_moteur.ilike.%${search}%`)
      : q;
  }

  async function loadBoites() {
    setLoading(true);

    let rowsQ = supabase
      .from("v_boites_dispo")
      .select("n_bv, num_interne_bv, ref_bv, num_interne_moteur, achat_bv, prix_vte_bv, date_vente_bv, resa_client_bv, date_resa_bv, stock, vendu, est_disponible, n_reception")
      .order("n_bv", { ascending: false })
      .limit(ROW_LIMIT);
    rowsQ = applySearch(rowsQ as any) as any;
    if (statut === "Disponible") rowsQ = rowsQ.eq("est_disponible", 1).is("resa_client_bv", null);
    if (statut === "Réservée") rowsQ = rowsQ.eq("est_disponible", 1).not("resa_client_bv", "is", null);
    if (statut === "Vendue") rowsQ = rowsQ.eq("est_disponible", 0);

    const countBase = () => applySearch(
      supabase.from("v_boites_dispo").select("*", { count: "exact", head: true }) as any
    );

    const [rowsRes, totalRes, dispoRes, reserveRes, venduRes] = await Promise.all([
      rowsQ,
      countBase(),
      countBase().eq("est_disponible", 1).is("resa_client_bv", null),
      countBase().eq("est_disponible", 1).not("resa_client_bv", "is", null),
      countBase().eq("est_disponible", 0),
    ]);

    setBoites(rowsRes.data || []);
    setCounts({
      total: totalRes.count || 0,
      dispo: dispoRes.count || 0,
      reserve: reserveRes.count || 0,
      vendu: venduRes.count || 0,
    });
    setLoading(false);
  }

  useEffect(() => { loadBoites(); }, [search, statut]);

  return (
    <div>
      <PageHeader title="Identification Boîtes de vitesse" description="Recherche et consultation du stock BV" />

      <div className="flex flex-wrap gap-3 mb-6">
        <Input
          placeholder="Rechercher (réf BV, num interne...)"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm bg-surface-alt border-border text-foreground placeholder:text-text-muted"
        />
        <select
          value={statut}
          onChange={(e) => setStatut(e.target.value)}
          className="border border-border rounded-lg px-3 py-2 text-sm bg-surface-alt text-foreground"
        >
          <option>Tous</option>
          <option>Disponible</option>
          <option>Réservée</option>
          <option>Vendue</option>
        </select>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card><CardContent className="p-4"><p className="text-xs text-text-dim font-semibold uppercase">Résultats</p><p className="text-2xl font-bold text-brand">{counts.total.toLocaleString("fr-FR")}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-text-dim font-semibold uppercase">Disponibles</p><p className="text-2xl font-bold text-emerald-600">{counts.dispo.toLocaleString("fr-FR")}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-text-dim font-semibold uppercase">Réservées</p><p className="text-2xl font-bold text-amber-600">{counts.reserve.toLocaleString("fr-FR")}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-text-dim font-semibold uppercase">Vendues</p><p className="text-2xl font-bold text-text-muted">{counts.vendu.toLocaleString("fr-FR")}</p></CardContent></Card>
      </div>
      {counts.total > boites.length && !loading && (
        <p className="text-xs text-text-muted mb-3">Affichage des {boites.length.toLocaleString("fr-FR")} dernières boîtes sur {counts.total.toLocaleString("fr-FR")} — affinez via la recherche.</p>
      )}

      {loading ? (
        <div className="text-center py-12 text-text-muted">Chargement...</div>
      ) : (
        <div className="bg-surface border border-border rounded-[14px] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-surface-alt text-text-dim text-xs uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">N°</th>
                  <th className="px-4 py-3 text-left">Réf BV</th>
                  <th className="px-4 py-3 text-left">Num interne</th>
                  <th className="px-4 py-3 text-left">Moteur lié</th>
                  <th className="px-4 py-3 text-right">Prix achat</th>
                  <th className="px-4 py-3 text-right">Prix vente</th>
                  <th className="px-4 py-3 text-center">Statut</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {boites.map((b) => (
                  <tr key={b.n_bv} className="hover:bg-surface-hover transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-text-muted">{b.n_bv}</td>
                    <td className="px-4 py-3 font-semibold text-foreground">{b.ref_bv || "—"}</td>
                    <td className="px-4 py-3 text-text-dim">{b.num_interne_bv || "—"}</td>
                    <td className="px-4 py-3 text-text-dim">{b.num_interne_moteur || "—"}</td>
                    <td className="px-4 py-3 text-right tabular-nums text-text-dim">
                      {b.achat_bv ? `${Math.round(b.achat_bv).toLocaleString("fr-FR")} €` : "—"}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-text-dim">
                      {b.prix_vte_bv ? `${Math.round(b.prix_vte_bv).toLocaleString("fr-FR")} €` : "—"}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {b.est_disponible === 0 ? (
                        <Badge className="bg-[rgba(148,163,184,0.15)] text-slate-600 border border-[rgba(148,163,184,0.25)] hover:bg-[rgba(148,163,184,0.20)]">Vendue</Badge>
                      ) : b.resa_client_bv ? (
                        <Badge className="bg-[rgba(251,191,36,0.10)] text-amber-600 border border-[rgba(251,191,36,0.20)] hover:bg-[rgba(251,191,36,0.15)]">Réservée</Badge>
                      ) : (
                        <Badge className="bg-[rgba(52,211,153,0.10)] text-emerald-600 border border-[rgba(52,211,153,0.20)] hover:bg-[rgba(52,211,153,0.15)]">Disponible</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {boites.length === 0 && (
            <p className="text-center py-10 text-text-muted italic">Aucune boîte trouvée</p>
          )}
        </div>
      )}
    </div>
  );
}
