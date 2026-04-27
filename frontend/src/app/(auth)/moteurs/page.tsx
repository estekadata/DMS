"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const ROW_LIMIT = 1000;

export default function MoteursPage() {
  const [search, setSearch] = useState("");
  const [statut, setStatut] = useState("Tous");
  const [moteurs, setMoteurs] = useState<any[]>([]);
  const [counts, setCounts] = useState({ total: 0, dispo: 0, reserve: 0, archive: 0 });
  const [loading, setLoading] = useState(false);

  function applySearch<T extends { or: (f: string) => T }>(q: T): T {
    return search
      ? q.or(`nom_type_moteur.ilike.%${search}%,code_moteur.ilike.%${search}%,num_serie.ilike.%${search}%`)
      : q;
  }

  async function loadMoteurs() {
    setLoading(true);

    let rowsQ = supabase
      .from("v_moteurs_dispo")
      .select("n_moteur, code_moteur, nom_type_moteur, num_serie, marque, energie, prix_achat_moteur, est_disponible, archiver, resa_client_moteur, num_reception")
      .order("n_moteur", { ascending: false })
      .limit(ROW_LIMIT);
    rowsQ = applySearch(rowsQ as any) as any;
    if (statut === "Disponible") rowsQ = rowsQ.eq("est_disponible", 1).is("resa_client_moteur", null);
    if (statut === "Réservé") rowsQ = rowsQ.eq("est_disponible", 1).not("resa_client_moteur", "is", null);
    if (statut === "Vendu/Archivé") rowsQ = rowsQ.eq("est_disponible", 0);

    const countBase = () => applySearch(
      supabase.from("v_moteurs_dispo").select("*", { count: "exact", head: true }) as any
    );

    const [rowsRes, totalRes, dispoRes, reserveRes, archiveRes] = await Promise.all([
      rowsQ,
      countBase(),
      countBase().eq("est_disponible", 1).is("resa_client_moteur", null),
      countBase().eq("est_disponible", 1).not("resa_client_moteur", "is", null),
      countBase().eq("est_disponible", 0),
    ]);

    const rows = rowsRes.data || [];

    // Fallback prix : pour les moteurs sans prix_achat_moteur, utiliser la moyenne de la réception
    const receptionIds = [...new Set(rows.map((m: any) => m.num_reception).filter(Boolean))] as number[];
    const avgByReception: Record<number, number> = {};
    if (receptionIds.length > 0) {
      const { data: recs } = await supabase
        .from("v_receptions")
        .select("n_reception, montant_total, nb_moteurs")
        .in("n_reception", receptionIds);
      (recs || []).forEach((r: any) => {
        if (r.montant_total && r.nb_moteurs && r.nb_moteurs > 0) {
          avgByReception[r.n_reception] = r.montant_total / r.nb_moteurs;
        }
      });
    }
    const enriched = rows.map((m: any) => ({
      ...m,
      prix_affiche: m.prix_achat_moteur && m.prix_achat_moteur > 0
        ? m.prix_achat_moteur
        : avgByReception[m.num_reception],
      prix_est_moyenne: !(m.prix_achat_moteur && m.prix_achat_moteur > 0) && !!avgByReception[m.num_reception],
    }));

    setMoteurs(enriched);
    setCounts({
      total: totalRes.count || 0,
      dispo: dispoRes.count || 0,
      reserve: reserveRes.count || 0,
      archive: archiveRes.count || 0,
    });
    setLoading(false);
  }

  useEffect(() => { loadMoteurs(); }, [search, statut]);

  return (
    <div>
      <PageHeader title="Identification Moteurs" description="Recherche et consultation du stock moteurs" />

      <div className="flex flex-wrap gap-3 mb-6">
        <Input
          placeholder="Rechercher (code moteur, num série...)"
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
          <option>Réservé</option>
          <option>Vendu/Archivé</option>
        </select>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card><CardContent className="p-4"><p className="text-xs text-text-dim font-semibold uppercase">Résultats</p><p className="text-2xl font-bold text-brand">{counts.total.toLocaleString("fr-FR")}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-text-dim font-semibold uppercase">Disponibles</p><p className="text-2xl font-bold text-emerald-600">{counts.dispo.toLocaleString("fr-FR")}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-text-dim font-semibold uppercase">Réservés</p><p className="text-2xl font-bold text-amber-600">{counts.reserve.toLocaleString("fr-FR")}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-text-dim font-semibold uppercase">Vendus/Archivés</p><p className="text-2xl font-bold text-text-muted">{counts.archive.toLocaleString("fr-FR")}</p></CardContent></Card>
      </div>
      {counts.total > moteurs.length && !loading && (
        <p className="text-xs text-text-muted mb-3">Affichage des {moteurs.length.toLocaleString("fr-FR")} derniers moteurs sur {counts.total.toLocaleString("fr-FR")} — affinez via la recherche.</p>
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
                  <th className="px-4 py-3 text-left">Code moteur</th>
                  <th className="px-4 py-3 text-left">Num série</th>
                  <th className="px-4 py-3 text-left">Marque</th>
                  <th className="px-4 py-3 text-left">Énergie</th>
                  <th className="px-4 py-3 text-right">Prix achat</th>
                  <th className="px-4 py-3 text-center">Statut</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {moteurs.map((m) => (
                  <tr key={m.n_moteur} className="hover:bg-surface-hover transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-text-muted">{m.n_moteur}</td>
                    <td className="px-4 py-3 font-semibold text-foreground">{m.nom_type_moteur || m.code_moteur || "—"}</td>
                    <td className="px-4 py-3 text-text-dim">{m.num_serie || "—"}</td>
                    <td className="px-4 py-3 text-text-dim">{m.marque || "—"}</td>
                    <td className="px-4 py-3 text-text-dim">{m.energie || "—"}</td>
                    <td className="px-4 py-3 text-right tabular-nums text-text-dim">
                      {m.prix_affiche ? (
                        <span title={m.prix_est_moyenne ? "Moyenne réception (prix individuel non saisi)" : "Prix d'achat saisi"}>
                          {Math.round(m.prix_affiche).toLocaleString("fr-FR")} €
                          {m.prix_est_moyenne && <span className="ml-1 text-text-muted">~</span>}
                        </span>
                      ) : "—"}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {m.archiver ? (
                        <Badge className="bg-[rgba(90,100,120,0.10)] text-text-muted border border-[rgba(90,100,120,0.20)] hover:bg-[rgba(90,100,120,0.15)]">Archivé</Badge>
                      ) : m.est_disponible === 0 ? (
                        <Badge className="bg-[rgba(148,163,184,0.15)] text-slate-600 border border-[rgba(148,163,184,0.25)] hover:bg-[rgba(148,163,184,0.20)]">Vendu</Badge>
                      ) : m.resa_client_moteur ? (
                        <Badge className="bg-[rgba(251,191,36,0.10)] text-amber-600 border border-[rgba(251,191,36,0.20)] hover:bg-[rgba(251,191,36,0.15)]">Réservé</Badge>
                      ) : (
                        <Badge className="bg-[rgba(52,211,153,0.10)] text-emerald-600 border border-[rgba(52,211,153,0.20)] hover:bg-[rgba(52,211,153,0.15)]">Disponible</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {moteurs.length === 0 && (
            <p className="text-center py-10 text-text-muted italic">Aucun moteur trouvé</p>
          )}
        </div>
      )}
    </div>
  );
}
