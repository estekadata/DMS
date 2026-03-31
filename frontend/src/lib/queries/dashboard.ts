import { supabase } from "@/lib/supabase";
import type { DashboardKpis } from "@/lib/types";

export async function getDashboardKpis(): Promise<DashboardKpis> {
  // Fetch KPIs in parallel
  const [moteurs, boites, reserves, bvReserves, ventesMois, ventesPrec, receptions, marge, prixMoy] = await Promise.all([
    // Moteurs stock
    supabase.from("v_moteurs_dispo").select("est_disponible", { count: "exact" }),
    // Boites stock
    supabase.from("v_boites_dispo").select("est_disponible", { count: "exact" }),
    // Moteurs reserves
    supabase.from("tbl_moteurs").select("n_moteur", { count: "exact" })
      .not("resa_client_moteur", "is", null)
      .is("n_expedition", null),
    // Boites reservees
    supabase.from("tbl_boites").select("n_bv", { count: "exact" })
      .not("resa_client_bv", "is", null)
      .eq("stock", true),
    // Ventes ce mois (use RPC for date-based queries)
    supabase.rpc("get_ventes_mois_count"),
    // Ventes mois precedent
    supabase.rpc("get_ventes_mois_prec_count"),
    // Receptions ce mois
    supabase.rpc("get_receptions_mois_count"),
    // Marge
    supabase.rpc("get_marge_mois"),
    // Prix moyens
    supabase.rpc("get_prix_moyens_mois"),
  ]);

  const motDispo = (moteurs.data || []).filter((r: { est_disponible: number }) => r.est_disponible === 1).length;
  const bvDispo = (boites.data || []).filter((r: { est_disponible: number }) => r.est_disponible === 1).length;

  return {
    mot_dispo: motDispo,
    mot_total: moteurs.count || 0,
    bv_dispo: bvDispo,
    bv_total: boites.count || 0,
    mot_reserves: reserves.count || 0,
    bv_reserves: bvReserves.count || 0,
    ventes_mois: (ventesMois.data as { n: number } | null)?.n || 0,
    ca_mois: (ventesMois.data as { ca: number } | null)?.ca || 0,
    ventes_mois_prec: (ventesPrec.data as { n: number } | null)?.n || 0,
    ca_mois_prec: (ventesPrec.data as { ca: number } | null)?.ca || 0,
    receptions_mois: (receptions.data as { n: number } | null)?.n || 0,
    mot_recus_mois: (receptions.data as { nb_mot: number } | null)?.nb_mot || 0,
    marge_mois: (marge.data as { marge: number } | null)?.marge || 0,
    marge_pct: (marge.data as { pct: number } | null)?.pct || 0,
    prix_vente_moy: (prixMoy.data as { prix_vente_moy: number } | null)?.prix_vente_moy || 0,
    prix_achat_moy: (prixMoy.data as { prix_achat_moy: number } | null)?.prix_achat_moy || 0,
  };
}
