"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type Besoin = {
  code_moteur: string;
  type_moteur: string;
  marque: string;
  energie: string;
  type_nom: string;
  type_modele: string;
  type_annee: string;
  nb_vendus_3m: number;
  nb_stock_dispo: number;
  prix_moy_achat_3m: number | null;
  delta: number;
};

const TABS = ["En manque", "En surstock", "Tout voir"] as const;
type Tab = (typeof TABS)[number];

export default function BesoinsPage() {
  const [tab, setTab] = useState<Tab>("En manque");
  const [search, setSearch] = useState("");
  const [besoins, setBesoins] = useState<Besoin[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const { data, error } = await supabase.rpc("get_besoins_moteurs", {
        p_limit: 500,
      });

      if (!error && data) {
        setBesoins(
          (data as Omit<Besoin, "delta">[]).map((r) => ({
            ...r,
            delta: r.nb_stock_dispo - r.nb_vendus_3m,
          }))
        );
      } else {
        console.error("get_besoins_moteurs error:", error);
        setBesoins([]);
      }
      setLoading(false);
    }
    load();
  }, []);

  const filtered = besoins
    .filter((b) => {
      if (tab === "En manque") return b.delta < 0;
      if (tab === "En surstock") return b.delta > 2;
      return true;
    })
    .filter((b) =>
      search
        ? b.code_moteur.toLowerCase().includes(search.toLowerCase()) ||
          b.marque?.toLowerCase().includes(search.toLowerCase()) ||
          b.type_nom?.toLowerCase().includes(search.toLowerCase())
        : true
    );

  const nbManque = besoins.filter((b) => b.delta < 0).length;
  const nbSurstock = besoins.filter((b) => b.delta > 2).length;

  return (
    <div>
      <PageHeader
        title="Analyse des besoins"
        icon="🎯"
        description="Besoins et surstock par référence moteur (ventes 3 derniers mois vs stock dispo)"
      />

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-gray-500 font-semibold uppercase">
              En manque
            </p>
            <p className="text-2xl font-bold text-red-600">{nbManque}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-gray-500 font-semibold uppercase">
              En surstock
            </p>
            <p className="text-2xl font-bold text-blue-600">{nbSurstock}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-gray-500 font-semibold uppercase">
              Total références
            </p>
            <p className="text-2xl font-bold text-gray-700">
              {besoins.length}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-5">
        <div className="flex bg-white rounded-lg shadow-sm border overflow-hidden">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium transition ${
                tab === t
                  ? "bg-[#C41E3A] text-white"
                  : "text-gray-600 hover:bg-gray-50"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        <Input
          placeholder="Filtrer par code, marque, type..."
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
                  <th className="px-4 py-3 text-left">Code moteur</th>
                  <th className="px-4 py-3 text-left">Type</th>
                  <th className="px-4 py-3 text-left">Marque</th>
                  <th className="px-4 py-3 text-left">Énergie</th>
                  <th className="px-4 py-3 text-center">Vendus (3 mois)</th>
                  <th className="px-4 py-3 text-center">Stock dispo</th>
                  <th className="px-4 py-3 text-center">Delta</th>
                  <th className="px-4 py-3 text-right">Prix moy. achat</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((b) => (
                  <tr key={b.code_moteur} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-semibold">
                      {b.code_moteur}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {b.type_moteur || "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {b.marque || "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {b.energie || "—"}
                    </td>
                    <td className="px-4 py-3 text-center tabular-nums">
                      {b.nb_vendus_3m}
                    </td>
                    <td className="px-4 py-3 text-center tabular-nums">
                      {b.nb_stock_dispo}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Badge
                        className={
                          b.delta < 0
                            ? "bg-red-100 text-red-700 hover:bg-red-100"
                            : b.delta > 2
                            ? "bg-blue-100 text-blue-700 hover:bg-blue-100"
                            : "bg-gray-100 text-gray-600 hover:bg-gray-100"
                        }
                      >
                        {b.delta > 0 ? `+${b.delta}` : b.delta}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-gray-600">
                      {b.prix_moy_achat_3m != null
                        ? `${b.prix_moy_achat_3m.toFixed(0)} €`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filtered.length === 0 && (
            <p className="text-center py-10 text-gray-400">Aucun résultat</p>
          )}
        </div>
      )}
    </div>
  );
}
