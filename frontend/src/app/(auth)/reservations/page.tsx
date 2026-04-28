"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const PAGE_SIZE = 200;

type Reservation = {
  id: number;
  code: string;
  clientId: number | null;
  clientLabel: string;
  date_reservation: string | null;
};

function parseClientId(raw: string | null | undefined): number | null {
  if (!raw) return null;
  const n = parseFloat(String(raw).replace(",", "."));
  return Number.isFinite(n) ? Math.round(n) : null;
}

export default function ReservationsPage() {
  const [tab, setTab] = useState<"moteurs" | "boites">("moteurs");
  const [rawSearch, setRawSearch] = useState("");
  const [search, setSearch] = useState("");
  const [rows, setRows] = useState<Reservation[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const reqIdRef = useRef(0);

  // Debounce search input
  useEffect(() => {
    const t = setTimeout(() => setSearch(rawSearch.trim()), 300);
    return () => clearTimeout(t);
  }, [rawSearch]);

  const fetchPage = useCallback(
    async (offset: number) => {
      const myReq = ++reqIdRef.current;

      // 1. If there's a search, find matching client IDs first
      let clientIds: number[] = [];
      if (search) {
        const { data: cliMatches } = await supabase
          .from("tbl_clients")
          .select("n_client")
          .or(`societe.ilike.%${search}%,nom_contact.ilike.%${search}%,nom_usage.ilike.%${search}%`)
          .limit(200);
        clientIds = (cliMatches || []).map((c: any) => c.n_client).filter(Boolean);
      }

      // 2. Build the query for the active tab
      const view = tab === "moteurs" ? "v_moteurs_dispo" : "v_boites_dispo";
      const dateCol = tab === "moteurs" ? "date_resa_moteur" : "date_resa_bv";
      const clientCol = tab === "moteurs" ? "resa_client_moteur" : "resa_client_bv";
      const codeCols =
        tab === "moteurs"
          ? ["nom_type_moteur", "code_moteur"]
          : ["ref_bv", "num_interne_bv"];

      const selectCols =
        tab === "moteurs"
          ? "n_moteur, nom_type_moteur, code_moteur, resa_client_moteur, date_resa_moteur"
          : "n_bv, ref_bv, num_interne_bv, resa_client_bv, date_resa_bv";

      const buildBase = () =>
        supabase.from(view).select(selectCols, { count: "exact" }).not(clientCol, "is", null);

      const buildCount = () =>
        supabase.from(view).select("*", { count: "exact", head: true }).not(clientCol, "is", null);

      let rowsQ = buildBase()
        .order(dateCol, { ascending: false, nullsFirst: false })
        .range(offset, offset + PAGE_SIZE - 1);
      let countQ = buildCount();

      if (search) {
        const filters: string[] = [];
        for (const col of codeCols) filters.push(`${col}.ilike.%${search}%`);
        if (clientIds.length) {
          // resa_client_* is TEXT and stored as "521.0" — match both formats
          const variants = clientIds
            .flatMap((id) => [`"${id}.0"`, `"${id}"`])
            .join(",");
          filters.push(`${clientCol}.in.(${variants})`);
        }
        const orStr = filters.join(",");
        rowsQ = rowsQ.or(orStr);
        countQ = countQ.or(orStr);
      }

      const [rowsRes, countRes] = await Promise.all([rowsQ, countQ]);
      if (myReq !== reqIdRef.current) return null; // stale

      const rawRows = (rowsRes.data as any[]) || [];

      // 3. Resolve client names for the displayed rows
      const idsToResolve = Array.from(
        new Set(rawRows.map((r) => parseClientId(r[clientCol])).filter((x): x is number => x !== null))
      );

      const clientMap: Record<number, string> = {};
      if (idsToResolve.length) {
        const { data: cliRes } = await supabase
          .from("tbl_clients")
          .select("n_client, societe, nom_contact, nom_usage")
          .in("n_client", idsToResolve);
        (cliRes || []).forEach((c: any) => {
          clientMap[c.n_client] =
            c.societe || c.nom_usage || c.nom_contact || `Client #${c.n_client}`;
        });
      }

      const mapped: Reservation[] = rawRows.map((r) => {
        const cid = parseClientId(r[clientCol]);
        const code =
          tab === "moteurs"
            ? r.nom_type_moteur || r.code_moteur || "—"
            : r.ref_bv || r.num_interne_bv || "—";
        return {
          id: tab === "moteurs" ? r.n_moteur : r.n_bv,
          code,
          clientId: cid,
          clientLabel: cid !== null ? clientMap[cid] || `Client #${cid}` : "—",
          date_reservation: tab === "moteurs" ? r.date_resa_moteur : r.date_resa_bv,
        };
      });

      return { rows: mapped, total: countRes.count || 0 };
    },
    [tab, search]
  );

  // Reset & load when tab or search changes
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      const result = await fetchPage(0);
      if (cancelled || result === null) return;
      setRows(result.rows);
      setTotal(result.total);
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, [fetchPage]);

  async function loadMore() {
    setLoadingMore(true);
    const result = await fetchPage(rows.length);
    if (result !== null) {
      setRows((prev) => [...prev, ...result.rows]);
      setTotal(result.total);
    }
    setLoadingMore(false);
  }

  const remaining = Math.max(0, total - rows.length);

  return (
    <div>
      <PageHeader title="Réservations" description="Gestion des réservations clients" />

      <div className="grid grid-cols-2 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-text-dim font-semibold uppercase">
              {search ? "Résultats" : "Réservations actives"}
            </p>
            <p className="text-2xl font-bold text-brand">{total.toLocaleString("fr-FR")}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-text-dim font-semibold uppercase">Affichées</p>
            <p className="text-2xl font-bold text-foreground">{rows.length.toLocaleString("fr-FR")}</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-5">
        <div className="flex bg-surface-alt rounded-lg border border-border overflow-hidden">
          {(["moteurs", "boites"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium transition-all ${
                tab === t ? "bg-brand text-white" : "text-text-dim hover:bg-surface-hover"
              }`}
            >
              {t === "moteurs" ? "Moteurs" : "Boîtes"}
            </button>
          ))}
        </div>
        <Input
          placeholder="Rechercher par code, société ou contact..."
          value={rawSearch}
          onChange={(e) => setRawSearch(e.target.value)}
          className="max-w-sm bg-surface-alt border-border text-foreground placeholder:text-text-muted"
        />
      </div>

      {loading ? (
        <div className="text-center py-12 text-text-muted">Chargement...</div>
      ) : (
        <>
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
                  {rows.map((r) => (
                    <tr key={`${tab}-${r.id}`} className="hover:bg-surface-hover transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-text-muted">{r.id}</td>
                      <td className="px-4 py-3 font-semibold text-foreground">{r.code}</td>
                      <td className="px-4 py-3">
                        {r.clientId !== null ? (
                          <Link
                            href={`/clients/${r.clientId}`}
                            className="text-brand hover:underline font-medium"
                          >
                            {r.clientLabel}
                          </Link>
                        ) : (
                          <span className="text-text-dim">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-text-dim">
                        {r.date_reservation
                          ? new Date(r.date_reservation).toLocaleDateString("fr-FR")
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <Badge className="bg-[rgba(251,191,36,0.10)] text-amber-600 border border-[rgba(251,191,36,0.20)] hover:bg-[rgba(251,191,36,0.15)]">
                          Active
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {rows.length === 0 && (
              <p className="text-center py-10 text-text-muted italic">Aucune réservation trouvée</p>
            )}
          </div>

          {remaining > 0 && (
            <div className="flex justify-center mt-5">
              <Button onClick={loadMore} disabled={loadingMore} variant="outline">
                {loadingMore
                  ? "Chargement..."
                  : `Charger plus (${remaining.toLocaleString("fr-FR")} restantes)`}
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
