"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type Besoin = {
  code_moteur: string;
  marque?: string;
  energie?: string;
  nb_en_stock: number;
  nb_commandes_actives: number;
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
      const { data, error } = await supabase
        .from("v_besoins_moteurs")
        .select("code_moteur, marque, energie, nb_en_stock, nb_commandes_actives, delta")
        .order("delta", { ascending: true })
        .limit(500);

      if (error) {
        // Fallback: compute from stock vs orders
        const { data: fallback } = await supabase
          .from("v_moteurs_dispo")
          .select("code_moteur, marque, energie, est_disponible")
          .limit(1000);

        if (fallback) {
          const grouped: Record<string, Besoin> = {};
          fallback.forEach((m: any) => {
            const k = m.code_moteur || "INCONNU";
            if (!grouped[k]) grouped[k] = { code_moteur: k, marque: m.marque, energie: m.energie, nb_en_stock: 0, nb_commandes_actives: 0, delta: 0 };
            if (m.est_disponible === 1) grouped[k].nb_en_stock++;
          });
          setBesoins(Object.values(grouped));
        }
      } else {
        setBesoins(data || []);
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
      search ? b.code_moteur.toLowerCase().includes(search.toLowerCase()) : true
    );

  const nbManque = besoins.filter((b) => b.delta < 0).length;
  const nbSurstock = besoins.filter((b) => b.delta > 2).length;

  return (
    <div>
      <PageHeader title="Analyse des besoins" icon="🎯" description="Besoins et surstock par référence moteur" />

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-gray-500 font-semibold uppercase">En manque</p>
            <p className="text-2xl font-bold text-red-600">{nbManque}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-gray-500 font-semibold uppercase">En surstock</p>
            <p className="text-2xl font-bold text-blue-600">{nbSurstock}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-gray-500 font-semibold uppercase">Total références</p>
            <p className="text-2xl font-bold text-gray-700">{besoins.length}</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-5">
        <div className="flex bg-white rounded-lg shadow-sm border overflow-hidden">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium transition ${tab === t ? "bg-[#C41E3A] text-white" : "text-gray-600 hover:bg-gray-50"}`}
            >
              {t}
            </button>
          ))}
        </div>
        <Input
          placeholder="Filtrer par code moteur..."
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
                  <th className="px-4 py-3 text-left">Marque</th>
                  <th className="px-4 py-3 text-left">Énergie</th>
                  <th className="px-4 py-3 text-center">En stock</th>
                  <th className="px-4 py-3 text-center">Commandes actives</th>
                  <th className="px-4 py-3 text-center">Delta</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((b) => (
                  <tr key={b.code_moteur} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-semibold">{b.code_moteur}</td>
                    <td className="px-4 py-3 text-gray-600">{b.marque || "—"}</td>
                    <td className="px-4 py-3 text-gray-600">{b.energie || "—"}</td>
                    <td className="px-4 py-3 text-center tabular-nums">{b.nb_en_stock}</td>
                    <td className="px-4 py-3 text-center tabular-nums">{b.nb_commandes_actives}</td>
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
