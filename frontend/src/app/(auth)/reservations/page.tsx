"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

const ROW_LIMIT = 1000;

type Reservation = {
  id: number;
  code: string;
  client: string;
  date_reservation: string | null;
};

export default function ReservationsPage() {
  const [tab, setTab] = useState<"moteurs" | "boites">("moteurs");
  const [rows, setRows] = useState<Reservation[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  async function load() {
    setLoading(true);

    if (tab === "moteurs") {
      const [rowsRes, countRes] = await Promise.all([
        supabase
          .from("v_moteurs_dispo")
          .select("n_moteur, nom_type_moteur, code_moteur, resa_client_moteur, date_resa_moteur")
          .not("resa_client_moteur", "is", null)
          .order("date_resa_moteur", { ascending: false, nullsFirst: false })
          .limit(ROW_LIMIT),
        supabase
          .from("v_moteurs_dispo")
          .select("*", { count: "exact", head: true })
          .not("resa_client_moteur", "is", null),
      ]);
      setRows((rowsRes.data || []).map((m: any) => ({
        id: m.n_moteur,
        code: m.nom_type_moteur || m.code_moteur || "—",
        client: m.resa_client_moteur || "",
        date_reservation: m.date_resa_moteur,
      })));
      setTotal(countRes.count || 0);
    } else {
      const [rowsRes, countRes] = await Promise.all([
        supabase
          .from("v_boites_dispo")
          .select("n_bv, ref_bv, num_interne_bv, resa_client_bv, date_resa_bv")
          .not("resa_client_bv", "is", null)
          .order("date_resa_bv", { ascending: false, nullsFirst: false })
          .limit(ROW_LIMIT),
        supabase
          .from("v_boites_dispo")
          .select("*", { count: "exact", head: true })
          .not("resa_client_bv", "is", null),
      ]);
      setRows((rowsRes.data || []).map((b: any) => ({
        id: b.n_bv,
        code: b.ref_bv || b.num_interne_bv || "—",
        client: b.resa_client_bv || "",
        date_reservation: b.date_resa_bv,
      })));
      setTotal(countRes.count || 0);
    }

    setLoading(false);
  }

  useEffect(() => { load(); }, [tab]);

  const filtered = rows.filter((r) => {
    if (!search) return true;
    const s = search.toLowerCase();
    return r.code.toLowerCase().includes(s) || r.client.toLowerCase().includes(s);
  });

  return (
    <div>
      <PageHeader title="Réservations" description="Gestion des réservations clients" />

      <div className="grid grid-cols-2 gap-4 mb-6">
        <Card><CardContent className="p-4"><p className="text-xs text-text-dim font-semibold uppercase">Réservations actives</p><p className="text-2xl font-bold text-brand">{total.toLocaleString("fr-FR")}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-text-dim font-semibold uppercase">Affichées</p><p className="text-2xl font-bold text-foreground">{filtered.length.toLocaleString("fr-FR")}</p></CardContent></Card>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-5">
        <div className="flex bg-surface-alt rounded-lg border border-border overflow-hidden">
          {(["moteurs", "boites"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium transition-all ${tab === t ? "bg-brand text-white" : "text-text-dim hover:bg-surface-hover"}`}
            >
              {t === "moteurs" ? "Moteurs" : "Boîtes"}
            </button>
          ))}
        </div>
        <Input
          placeholder="Rechercher par code ou client..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-xs bg-surface-alt border-border text-foreground placeholder:text-text-muted"
        />
      </div>

      {total > rows.length && !loading && (
        <p className="text-xs text-text-muted mb-3">Affichage des {rows.length.toLocaleString("fr-FR")} dernières réservations sur {total.toLocaleString("fr-FR")} — affinez via la recherche.</p>
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
                  <th className="px-4 py-3 text-left">{tab === "moteurs" ? "Code moteur" : "Réf BV"}</th>
                  <th className="px-4 py-3 text-left">Client</th>
                  <th className="px-4 py-3 text-left">Date réservation</th>
                  <th className="px-4 py-3 text-center">Statut</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((r) => (
                  <tr key={r.id} className="hover:bg-surface-hover transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-text-muted">{r.id}</td>
                    <td className="px-4 py-3 font-semibold text-foreground">{r.code}</td>
                    <td className="px-4 py-3 text-text-dim">{r.client || "—"}</td>
                    <td className="px-4 py-3 text-text-dim">{r.date_reservation ? new Date(r.date_reservation).toLocaleDateString("fr-FR") : "—"}</td>
                    <td className="px-4 py-3 text-center">
                      <Badge className="bg-[rgba(251,191,36,0.10)] text-amber-600 border border-[rgba(251,191,36,0.20)] hover:bg-[rgba(251,191,36,0.15)]">Active</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filtered.length === 0 && (
            <p className="text-center py-10 text-text-muted italic">Aucune réservation trouvée</p>
          )}
        </div>
      )}
    </div>
  );
}
