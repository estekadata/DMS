export interface DashboardKpis {
  mot_dispo: number;
  mot_total: number;
  bv_dispo: number;
  bv_total: number;
  mot_reserves: number;
  bv_reserves: number;
  ventes_mois: number;
  ca_mois: number;
  ventes_mois_prec: number;
  ca_mois_prec: number;
  receptions_mois: number;
  mot_recus_mois: number;
  marge_mois: number;
  marge_pct: number;
  prix_vente_moy: number;
  prix_achat_moy: number;
}

export interface Moteur {
  n_moteur: number;
  num_interne_moteur?: string;
  code_moteur?: string;
  num_serie?: string;
  modele_saisi?: string;
  prix_achat_moteur?: number;
  etat_moteur?: string;
  observations?: string;
  resa_client_moteur?: string;
  date_resa_moteur?: string;
  marque?: string;
  energie?: string;
  statut: string;
  fournisseur?: string;
  date_achat?: string;
}

export interface Boite {
  n_bv: number;
  num_interne_bv?: string;
  ref_bv?: string;
  num_interne_moteur?: string;
  achat_bv?: number;
  prix_vte_bv?: number;
  observations_bv?: string;
  resa_client_bv?: string;
  date_resa_bv?: string;
  statut: string;
  emplacement?: string;
  fournisseur?: string;
  date_achat?: string;
}

export interface Reception {
  n_reception: number;
  fournisseur?: string;
  date_achat?: string;
  montant_ht?: number;
  nb_moteurs: number;
  nb_boites: number;
  nb_pieces: number;
}

export interface Expedition {
  n_expedition: number;
  client?: string;
  date_chargement?: string;
  montant_ht?: number;
  nb_moteurs: number;
  nb_boites: number;
}

export interface BesoinMoteur {
  code_moteur: string;
  type_moteur?: string;
  marque?: string;
  energie?: string;
  type_nom?: string;
  type_modele?: string;
  type_annee?: string;
  nb_vendus_3m: number;
  nb_stock_dispo: number;
  score_urgence: number;
  prix_moy_achat_3m?: number;
}

export interface PieceDetachee {
  categorie: string;
  marque?: string;
  reference: string;
  modele?: string;
  stock: number;
}

export interface KpiMeta {
  label: string;
  color: string;
  icon: string;
  fmt: "int" | "money" | "pct";
}

export const KPI_CATALOG: Record<string, KpiMeta> = {
  mot_dispo:       { label: "Moteurs en stock",       color: "emerald", icon: "📦", fmt: "int" },
  bv_dispo:        { label: "Boîtes en stock",        color: "emerald", icon: "⚙️", fmt: "int" },
  mot_reserves:    { label: "Moteurs réservés",        color: "amber",   icon: "🔒", fmt: "int" },
  bv_reserves:     { label: "Boîtes réservées",        color: "amber",   icon: "🔒", fmt: "int" },
  ventes_mois:     { label: "Ventes du mois",          color: "red",     icon: "📈", fmt: "int" },
  ca_mois:         { label: "CA du mois",              color: "red",     icon: "💰", fmt: "money" },
  receptions_mois: { label: "Réceptions du mois",      color: "blue",    icon: "📥", fmt: "int" },
  marge_mois:      { label: "Marge du mois",           color: "emerald", icon: "💵", fmt: "money" },
  marge_pct:       { label: "Marge du mois (%)",       color: "emerald", icon: "📊", fmt: "pct" },
};

export const DEFAULT_KPIS = [
  "mot_dispo", "bv_dispo", "mot_reserves", "ventes_mois",
  "ca_mois", "marge_mois", "receptions_mois", "marge_pct",
];
