"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

type Reservation = {
  n_reservation: number;
  n_moteur?: number;
  n_bv?: number;
  code_moteur?: string;
  code_bv?: string;
  client?: string;
  date_reservation?: string;
  date_expiration?: string;
  statut?: string;
  type_piece: "moteur" | "bv";
};

export default function ReservationsPage() {
  const [tab, setTab] = useState<"moteurs" | "boites">("moteurs");
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  async function load() {
    setLoading(true);
    const view = tab === "moteurs" ? "v_reservations_moteurs" : "v_reservations_boites";
    const { data } = await supabase
      .from(view)
      .select("*")
      .order("date_reservation", { ascending: false })
      .limit(300);
    setReservations((data || []).map((r: any) => ({ ...r, type_piece: tab === "moteurs" ? "moteur" : "bv" })));
    setLoading(false);
  }

  useEffect(() => { load(); }, [tab]);

  async function cancelReservation(id: number) {
    if (!confirm("Annuler cette réservation ?")) return;
    const table = tab === "moteurs" ? "tbl_reservations_moteurs" : "tbl_reservations_boites";
    await supabase.from(table).update({ statut: "Annulée" }).eq("n_reservation", id);
    load();
  }

  const filtered = reservations.filter((r) => {
    if (!search) return true;
    const code = tab === "moteurs" ? r.code_moteur : r.code_bv;
    return (
      (code || "").toLowerCase().includes(search.toLowerCase()) ||
      (r.client || "").toLowerCase().includes(search.toLowerCase())
    );
  });

  const nbActives = reservations.filter((r) => r.statut === "Active" || !r.statut).length;

  return (
    <div>
      <PageHeader title="Réservations" icon="📋" description="Gestion des réservations clients" />

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card><CardContent className="p-4"><p className="text-xs text-gray-500 font-semibold uppercase">Réservations actives</p><p className="text-2xl font-bold text-[#C41E3A]">{nbActives}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-gray-500 font-semibold uppercase">Total ({tab})</p><p className="text-2xl font-bold text-gray-700">{reservations.length}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-xs text-gray-500 font-semibold uppercase">Annulées</p><p className="text-2xl font-bold text-gray-400">{reservations.filter((r) => r.statut === "Annulée").length}</p></CardContent></Card>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-5">
        <div className="flex bg-white rounded-lg shadow-sm border overflow-hidden">
          {(["moteurs", "boites"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium transition ${tab === t ? "bg-[#C41E3A] text-white" : "text-gray-600 hover:bg-gray-50"}`}
            >
              {t === "moteurs" ? "Moteurs" : "Boîtes"}
            </button>
          ))}
        </div>
        <Input
          placeholder="Rechercher par code ou client..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-xs"
        />
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
                  <th className="px-4 py-3 text-left">{tab === "moteurs" ? "Code moteur" : "Code BV"}</th>
                  <th className="px-4 py-3 text-left">Client</th>
                  <th className="px-4 py-3 text-left">Date réservation</th>
                  <th className="px-4 py-3 text-left">Expiration</th>
                  <th className="px-4 py-3 text-center">Statut</th>
                  <th className="px-4 py-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((r) => (
                  <tr key={r.n_reservation} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-gray-400">{r.n_reservation}</td>
                    <td className="px-4 py-3 font-semibold">{(tab === "moteurs" ? r.code_moteur : r.code_bv) || "—"}</td>
                    <td className="px-4 py-3">{r.client || "—"}</td>
                    <td className="px-4 py-3 text-gray-600">{r.date_reservation ? new Date(r.date_reservation).toLocaleDateString("fr-FR") : "—"}</td>
                    <td className="px-4 py-3 text-gray-600">{r.date_expiration ? new Date(r.date_expiration).toLocaleDateString("fr-FR") : "—"}</td>
                    <td className="px-4 py-3 text-center">
                      <Badge
                        className={
                          r.statut === "Annulée"
                            ? "bg-gray-100 text-gray-500 hover:bg-gray-100"
                            : "bg-amber-100 text-amber-700 hover:bg-amber-100"
                        }
                      >
                        {r.statut || "Active"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {r.statut !== "Annulée" && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-red-600 border-red-200 hover:bg-red-50 text-xs"
                          onClick={() => cancelReservation(r.n_reservation)}
                        >
                          Annuler
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filtered.length === 0 && (
            <p className="text-center py-10 text-gray-400">Aucune réservation trouvée</p>
          )}
        </div>
      )}
    </div>
  );
}
