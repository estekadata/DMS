#!/usr/bin/env python3
"""
Sync incrémental Access (.accdb) -> Supabase Postgres.

Usage:
    # Mode preview (dry-run, ne modifie rien) :
    python sync_access.py --accdb /chemin/vers/base.accdb --mode preview

    # Mode apply (effectue les UPSERT) :
    python sync_access.py --accdb /chemin/vers/base.accdb --mode apply --user toi@example.com

Sortie : JSON sur stdout (consommable par l'API Next.js).

Pré-requis :
    - mdbtools installé (apt install mdbtools)
    - pip install pandas sqlalchemy psycopg2-binary
    - env DATABASE_URL = URL Postgres Supabase (sinon valeur par défaut hardcodée plus bas)
"""

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# ============================================
# CONFIGURATION
# ============================================

DEFAULT_DATABASE_URL = (
    "postgresql://postgres.ybaqkghlphxvkjmvtcly:1QoAroELqbzQDh9v"
    "@aws-1-eu-west-1.pooler.supabase.com:6543/postgres"
)
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)

# ============================================
# CONFIG TABLES — la "table des tables"
#
# Pour chaque table on déclare :
#   - access_table  : nom EXACT dans le .accdb (avec espaces)
#   - target        : nom Supabase
#   - strategy      : 'incremental_datemodif' | 'incremental_date_metier' | 'full_reload'
#   - pk            : tuple des colonnes Supabase qui composent la PK
#   - date_pivot    : (Access, Supabase) pour les stratégies incrémentales (None pour full_reload)
#                     Pour MOTEURS on prend la max des deux dates (gérée à part).
#   - mapping       : dict { colonne Access -> colonne Supabase }
# ============================================

TABLES_CONFIG: List[Dict[str, Any]] = [
    # ---------- Référentiels (full reload, UPSERT par PK) ----------
    {
        "access_table": "tbl Affectations",
        "target": "tbl_affectations",
        "strategy": "full_reload",
        "pk": ("n_affectation",),
        "date_pivot": None,
        "mapping": {
            "N_Affectation": "n_affectation",
            "Nom Affectation": "nom_affectation",
            "SélectionAffectation": "selection_affectation",
        },
    },
    {
        "access_table": "tbl Emplacements",
        "target": "tbl_emplacements",
        "strategy": "full_reload",
        "pk": ("id_emplacement",),
        "date_pivot": None,
        "mapping": {
            "IDEmplacement": "id_emplacement",
            "NomEmplacement": "nom_emplacement",
            "SélectionEmplacement": "selection_emplacement",
        },
    },
    {
        "access_table": "tbl Energie",
        "target": "tbl_energie",
        "strategy": "full_reload",
        "pk": ("n_energie",),
        "date_pivot": None,
        "mapping": {
            "N_Energie": "n_energie",
            "Nom Energie": "nom_energie",
            "Nom Energie Anglais": "nom_energie_anglais",
        },
    },
    {
        "access_table": "tbl Etats divers",
        "target": "tbl_etats_divers",
        "strategy": "full_reload",
        "pk": ("n_etat",),
        "date_pivot": None,
        "mapping": {
            "N_Etat": "n_etat",
            "Etat": "etat",
            "EtatAnglais": "etat_anglais",
            "SélectionEtat": "selection_etat",
            "Abréviation": "abreviation",
        },
    },
    {
        "access_table": "tbl Marques",
        "target": "tbl_marques",
        "strategy": "full_reload",
        "pk": ("n_marque",),
        "date_pivot": None,
        "mapping": {
            "N_Marque": "n_marque",
            "Nom Marque": "nom_marque",
            "SélectionMarque": "selection_marque",
        },
    },
    {
        "access_table": "tbl Pays",
        "target": "tbl_pays",
        "strategy": "full_reload",
        "pk": ("n_pays",),
        "date_pivot": None,
        "mapping": {
            "N_Pays": "n_pays",
            "Nom Pays": "nom_pays",
            "SélectionPays": "selection_pays",
        },
    },
    {
        "access_table": "tbl Types moteurs",
        "target": "tbl_types_moteurs",
        "strategy": "full_reload",
        "pk": ("n_type_moteur",),
        "date_pivot": None,
        "mapping": {
            "N_TypeMoteur": "n_type_moteur",
            "N_marque": "n_marque",
            "AvecSpécif": "avec_specif",
            "Nom TypeMoteur": "nom_type_moteur",
            "Modèle TypeMoteur": "modele_type_moteur",
            "N_Energie": "n_energie",
            "ObsEnergie": "obs_energie",
            "Année": "annee",
            "Particularité TypeMoteur": "particularite_type_moteur",
            "EquivalenceTypeMoteur": "equivalence_type_moteur",
            "PrixVenteMBV": "prix_vente_mbv",
            "PrixVenteMSeul": "prix_vente_m_seul",
            "HSCode": "hs_code",
            "PrixAchatBaseTypeMot": "prix_achat_base_type_mot",
        },
    },
    {
        "access_table": "tbl Fournisseurs",
        "target": "tbl_fournisseurs",
        "strategy": "full_reload",
        "pk": ("n_fournisseur",),
        "date_pivot": None,
        "mapping": {
            "N_Fournisseur": "n_fournisseur",
            "NomFournisseur": "nom_fournisseur",
            "ContactFourniss": "contact_fourniss",
            "Adresse1Fourniss": "adresse1_fourniss",
            "Adresse2Fourniss": "adresse2_fourniss",
            "CPFourniss": "cp_fourniss",
            "VilleFourniss": "ville_fourniss",
            "TélFourniss": "tel_fourniss",
            "FaxFourniss": "fax_fourniss",
            "PortFousniss": "port_fourniss",
            "MailFourniss": "mail_fourniss",
            "Autres infos": "autres_infos",
            "Actionnaire": "actionnaire",
            "Caréco": "careco",
            "N°Attribué": "n_attribue",
            "Afficher": "afficher",
        },
    },
    {
        "access_table": "tbl Clients",
        "target": "tbl_clients",
        "strategy": "full_reload",
        "pk": ("n_client",),
        "date_pivot": None,
        "mapping": {
            "N_client": "n_client",
            "Société": "societe",
            "TitreContact": "titre_contact",
            "NomContact": "nom_contact",
            "PrénomContact": "prenom_contact",
            "NomUsage": "nom_usage",
            "Adresse": "adresse",
            "Ville": "ville",
            "CodePostal": "code_postal",
            "Pays": "pays",
            "Tél": "tel",
            "Fax": "fax",
            "E-mail": "email",
            "Remarques": "remarques",
            "E/R": "e_r",
            "AfficherDéroulant": "afficher_deroulant",
            "Ident TVA": "ident_tva",
            "N_regroupClt": "n_regroup_clt",
        },
    },
    # ---------- Tables avec date métier (incrémental + filet 7 jours) ----------
    {
        "access_table": "tbl RECEPTIONS",
        "target": "tbl_receptions",
        "strategy": "incremental_date_metier",
        "pk": ("n_reception",),
        "date_pivot": ("DateAchat", "date_achat"),
        "mapping": {
            "N_réception": "n_reception",
            "N_fournisseur": "n_fournisseur",
            "DateAchat": "date_achat",
            "MontantHT": "montant_ht",
            "Facturé": "facture",
            "DateFactureFourniss": "date_facture_fourniss",
            "RéceptionTerminée": "reception_terminee",
            "DossierClassé": "dossier_classe",
            "Liste grillagés": "liste_grillages",
            "Autres info": "autres_info",
        },
    },
    {
        "access_table": "tbl EXPEDITIONS",
        "target": "tbl_expeditions",
        "strategy": "incremental_date_metier",
        "pk": ("n_expedition",),
        "date_pivot": ("DateChargement", "date_chargement"),
        "mapping": {
            "N_Expédition": "n_expedition",
            "N_client": "n_client",
            "DateChargement": "date_chargement",
            "TypeContainer": "type_container",
            "RéfContainer": "ref_container",
            "N° plomb": "n_plomb",
            "NbCartons": "nb_cartons",
            "NBPalettes": "nb_palettes",
            "Poids": "poids",
            "TareContainer": "tare_container",
            "N°Transitaire": "n_transitaire",
            "MontantHT": "montant_ht",
            "Autres info": "autres_info",
            "Num facture": "num_facture",
            "ExpéditionTerminée": "expedition_terminee",
            "ClôtureDossier": "cloture_dossier",
            "MoteursComplétés": "moteurs_completes",
            "FraisManut": "frais_manut",
            "CFR": "cfr",
            "PetitesPièces": "petites_pieces",
        },
    },
    {
        "access_table": "tbl FACTURES",
        "target": "tbl_factures",
        "strategy": "incremental_date_metier",
        "pk": ("num_piece",),
        "date_pivot": ("Date Facture", "date_facture"),
        "mapping": {
            "Num Pièce": "num_piece",
            "N_Client": "n_client",
            "N_Expédition": "n_expedition",
            "Type de pièce": "type_de_piece",
            "Date Facture": "date_facture",
            "AnnéeFact": "annee_fact",
            "RéfContainer": "ref_container",
            "EXPORT": "export",
            "EXP-CEE": "exp_cee",
            "EXP-TVA": "exp_tva",
            "R-TVA": "r_tva",
            "R-CEE": "r_cee",
            "SUSP-TVA": "susp_tva",
            "AUTRE PREST": "autre_prest",
            "PORT-TVA": "port_tva",
            "PORT-EXO": "port_exo",
            "EX A num1": "ex_a_num1",
            "EX A": "ex_a",
            "Connaissements": "connaissements",
            "DEB": "deb",
            "FactureAcquittée": "facture_acquittee",
            "ResteASolder": "reste_a_solder",
            "Transitaire": "transitaire",
            "TransitaireHorsListe": "transitaire_hors_liste",
            "ObservationsFacture": "observations_facture",
            "DossierClassé": "dossier_classe",
            "RelanceTransit": "relance_transit",
        },
    },
    # ---------- Tables principales (incrémental sur datemodif) ----------
    {
        "access_table": "tbl MOTEURS",
        "target": "tbl_moteurs",
        "strategy": "incremental_datemodif",
        "pk": ("n_moteur",),
        # Pour MOTEURS on prend max(date_modif, date_modif2) côté Supabase
        "date_pivot": ("DateModif", "date_modif"),
        "date_pivot_extra": ("DateModif2", "date_modif2"),
        "mapping": {
            "N_moteur": "n_moteur",
            "NumInterneMoteur": "num_interne_moteur",
            "NumRéception": "num_reception",
            "N_TypeMoteur": "n_type_moteur",
            "NumSérie": "num_serie",
            "ModèleSaisi": "modele_saisi",
            "CompoMoteur": "compo_moteur",
            "InfoBV": "info_bv",
            "TypeBV": "type_bv",
            "NumInterneBV": "num_interne_bv",
            "N_Affectation": "n_affectation",
            "RéfPI": "ref_pi",
            "TypePI": "type_pi",
            "EtatMoteur": "etat_moteur",
            "EtatCarter": "etat_carter",
            "Observations": "observations",
            "PrixAchatMoteur": "prix_achat_moteur",
            "DateRésaMoteur": "date_resa_moteur",
            "RésaClientMoteur": "resa_client_moteur",
            "Utilisateur": "utilisateur",
            "DateModif": "date_modif",
            "PointageInventaire": "pointage_inventaire",
            "Pointage2": "pointage2",
            "Alternateur": "alternateur",
            "Démarreur": "demarreur",
            "Carburateur": "carburateur",
            "Allumeur": "allumeur",
            "PAV": "pav",
            "PompeInj": "pompe_inj",
            "Turbo": "turbo",
            "Injecteurs": "injecteurs",
            "Compresseur": "compresseur",
            "PDA": "pda",
            "Embrayage": "embrayage",
            "Autre": "autre",
            "GélocMot": "geloc_mot",
            "CompoInit": "compo_init",
            "PoidsMoteur": "poids_moteur",
            "DateModif2": "date_modif2",
            "UtilisateurModif": "utilisateur_modif",
            "SélectionMoteurTble": "selection_moteur_tble",
            "CodeMoteur": "code_moteur",
            "DateSortie": "date_sortie",
            "Archiver": "archiver",
            "N_Expédition": "n_expedition",
        },
    },
    {
        "access_table": "tbl BOITES",
        "target": "tbl_boites",
        "strategy": "incremental_datemodif",
        "pk": ("n_bv",),
        "date_pivot": ("DateModif", "date_modif"),
        "mapping": {
            "N_BV": "n_bv",
            "NumInterneBV": "num_interne_bv",
            "N_réception": "n_reception",
            "TypeBV": "type_bv",
            "RéfBV": "ref_bv",
            "NumInterneMoteur": "num_interne_moteur",
            "AchatBV": "achat_bv",
            "DateRésaBV": "date_resa_bv",
            "RésaClientBV": "resa_client_bv",
            "ObservationsBV": "observations_bv",
            "Utilisateur": "utilisateur",
            "DateModif": "date_modif",
            "IDEmplacement": "id_emplacement",
            "PrixVteBV": "prix_vte_bv",
            "DateVenteBV": "date_vente_bv",
            "Stock": "stock",
            "Vendu": "vendu",
            "PointageInventaire": "pointage_inventaire",
        },
    },
]

# Marge de sécurité pour incremental_date_metier : on rejoue les N derniers jours
SAFETY_BACKFILL_DAYS = 7

# ============================================
# UTILS
# ============================================


def log(msg: str) -> None:
    """Log sur stderr pour ne pas polluer le JSON de stdout."""
    print(f"[sync] {msg}", file=sys.stderr, flush=True)


def check_mdbtools() -> None:
    if shutil.which("mdb-export") is None or shutil.which("mdb-tables") is None:
        raise RuntimeError(
            "mdbtools introuvable. Installe-le : sudo apt install mdbtools"
        )


def list_access_tables(accdb_path: Path) -> List[str]:
    out = subprocess.run(
        ["mdb-tables", "-1", str(accdb_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return [t for t in out.stdout.splitlines() if t.strip()]


def read_access_table(accdb_path: Path, table: str) -> pd.DataFrame:
    """Exporte une table Access en CSV via mdb-export, retourne un DataFrame."""
    proc = subprocess.run(
        ["mdb-export", "-D", "%Y-%m-%d %H:%M:%S", str(accdb_path), table],
        capture_output=True,
        check=True,
    )
    # mdb-export renvoie en UTF-8 (par défaut sur les .accdb modernes)
    csv_text = proc.stdout.decode("utf-8", errors="replace")
    if not csv_text.strip():
        return pd.DataFrame()
    return pd.read_csv(io.StringIO(csv_text), low_memory=False)


def clean_dataframe(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """Garde uniquement les colonnes mappées, renomme, normalise NaN -> None."""
    existing = [c for c in mapping.keys() if c in df.columns]
    df = df[existing].copy()
    df.rename(columns={k: mapping[k] for k in existing}, inplace=True)

    # Normalise les NaN/strings vides en None
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].apply(
                lambda x: None
                if (pd.isna(x) or str(x).strip() in ("", "nan", "None"))
                else (str(x).strip() if isinstance(x, str) else x)
            )
        else:
            df[col] = df[col].where(pd.notna(df[col]), None)
    return df


def get_supabase_state(
    engine: Engine, target: str, pk: Tuple[str, ...], date_cols: List[str]
) -> Tuple[Optional[datetime], set]:
    """
    Retourne (max_date, set des PKs existantes).
    max_date = max sur date_cols (tableau de noms de colonnes Supabase).
    """
    # Max date
    max_date: Optional[datetime] = None
    if date_cols:
        greatest = (
            f"GREATEST({', '.join(date_cols)})" if len(date_cols) > 1 else date_cols[0]
        )
        try:
            row = engine.execute(text(f"SELECT MAX({greatest}) FROM {target}")).first()
            max_date = row[0] if row else None
        except Exception:
            with engine.connect() as conn:
                row = conn.execute(
                    text(f"SELECT MAX({greatest}) FROM {target}")
                ).first()
                max_date = row[0] if row else None

    # Set des PKs existantes
    pk_cols = ", ".join(pk)
    existing_pks: set = set()
    with engine.connect() as conn:
        rs = conn.execute(text(f"SELECT {pk_cols} FROM {target}"))
        for r in rs:
            existing_pks.add(tuple(r) if len(pk) > 1 else r[0])
    return max_date, existing_pks


def filter_incremental(
    df: pd.DataFrame,
    last_date: Optional[datetime],
    date_cols: List[str],
    backfill_days: int = 0,
) -> pd.DataFrame:
    """Garde les lignes dont au moins une date_col > (last_date - backfill_days)."""
    if not date_cols or last_date is None:
        return df  # première sync : on prend tout

    cutoff = last_date - timedelta(days=backfill_days)
    mask = pd.Series(False, index=df.index)
    for col in date_cols:
        if col in df.columns:
            col_dt = pd.to_datetime(df[col], errors="coerce")
            mask = mask | (col_dt > cutoff)
    return df[mask].copy()


def upsert_dataframe(
    engine: Engine,
    target: str,
    df: pd.DataFrame,
    pk: Tuple[str, ...],
    batch_size: int = 500,
) -> Tuple[int, int]:
    """
    UPSERT par batch via INSERT ... ON CONFLICT (pk) DO UPDATE.
    Retourne (rows_inserted_or_updated, errors).
    """
    if df.empty:
        return 0, 0

    cols = list(df.columns)
    col_list = ", ".join(f'"{c}"' for c in cols)
    placeholders = ", ".join(f":{c}" for c in cols)
    pk_list = ", ".join(f'"{c}"' for c in pk)
    update_set = ", ".join(
        f'"{c}" = EXCLUDED."{c}"' for c in cols if c not in pk
    )

    if update_set:
        sql = (
            f"INSERT INTO {target} ({col_list}) VALUES ({placeholders}) "
            f"ON CONFLICT ({pk_list}) DO UPDATE SET {update_set}"
        )
    else:
        # Cas table avec uniquement des colonnes PK
        sql = (
            f"INSERT INTO {target} ({col_list}) VALUES ({placeholders}) "
            f"ON CONFLICT ({pk_list}) DO NOTHING"
        )

    affected = 0
    errors = 0
    with engine.begin() as conn:
        for i in range(0, len(df), batch_size):
            chunk = df.iloc[i : i + batch_size]
            payload = [
                {c: (None if pd.isna(v) else v) for c, v in row.items()}
                for row in chunk.to_dict(orient="records")
            ]
            try:
                conn.execute(text(sql), payload)
                affected += len(payload)
            except Exception as e:
                errors += len(payload)
                log(f"  ⚠️  batch {i}-{i+batch_size} ERREUR: {e}")
    return affected, errors


# ============================================
# CŒUR : process_table
# ============================================


def process_table(
    engine: Engine,
    accdb_path: Path,
    cfg: Dict[str, Any],
    mode: str,
    user_email: Optional[str],
) -> Dict[str, Any]:
    """
    Traite une table : retourne les stats {new, updated, total, errors, ...}.
    En mode 'apply' fait l'UPSERT et insère un import_log.
    """
    started = datetime.utcnow()
    target = cfg["target"]
    strategy = cfg["strategy"]
    pk = cfg["pk"]
    mapping = cfg["mapping"]

    log(f"→ {cfg['access_table']} ({strategy})")

    # 1. Lire la table Access
    df_raw = read_access_table(accdb_path, cfg["access_table"])
    rows_read_total = len(df_raw)

    if df_raw.empty:
        return {
            "table": target,
            "access_table": cfg["access_table"],
            "strategy": strategy,
            "rows_read": 0,
            "new": 0,
            "updated": 0,
            "total": 0,
            "errors": 0,
            "applied": False,
        }

    # 2. Nettoyer / mapper colonnes
    df = clean_dataframe(df_raw, mapping)

    # 3. Stratégie de filtrage
    date_pivot_supabase: List[str] = []
    if cfg.get("date_pivot"):
        date_pivot_supabase.append(cfg["date_pivot"][1])
    if cfg.get("date_pivot_extra"):
        date_pivot_supabase.append(cfg["date_pivot_extra"][1])

    last_date, existing_pks = get_supabase_state(
        engine, target, pk, date_pivot_supabase
    )

    if strategy == "incremental_datemodif":
        df = filter_incremental(df, last_date, date_pivot_supabase, backfill_days=0)
    elif strategy == "incremental_date_metier":
        df = filter_incremental(
            df, last_date, date_pivot_supabase, backfill_days=SAFETY_BACKFILL_DAYS
        )
    # full_reload : on garde tout

    # 4. Compter new vs updated
    if not df.empty:
        if len(pk) == 1:
            df_pks = df[pk[0]].apply(lambda v: v if not pd.isna(v) else None)
            is_existing = df_pks.apply(lambda v: v in existing_pks)
        else:
            df_pks = df[list(pk)].apply(lambda r: tuple(r), axis=1)
            is_existing = df_pks.apply(lambda v: v in existing_pks)
        n_updated = int(is_existing.sum())
        n_new = int(len(df) - n_updated)
    else:
        n_updated = 0
        n_new = 0

    result = {
        "table": target,
        "access_table": cfg["access_table"],
        "strategy": strategy,
        "rows_read": rows_read_total,
        "new": n_new,
        "updated": n_updated,
        "total": n_new + n_updated,
        "errors": 0,
        "applied": False,
        "last_sync": last_date.isoformat() if last_date else None,
    }

    # 5. Mode apply : UPSERT + log
    if mode == "apply" and not df.empty:
        affected, errors = upsert_dataframe(engine, target, df, pk)
        result["errors"] = errors
        result["applied"] = True

        # Update sync_metadata
        max_date_in_batch = None
        for c in date_pivot_supabase:
            if c in df.columns:
                col_dt = pd.to_datetime(df[c], errors="coerce")
                m = col_dt.max()
                if pd.notna(m):
                    if max_date_in_batch is None or m > max_date_in_batch:
                        max_date_in_batch = m
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                INSERT INTO sync_metadata (table_name, last_sync_at, last_max_date, last_user)
                VALUES (:t, NOW(), :m, :u)
                ON CONFLICT (table_name) DO UPDATE
                SET last_sync_at = NOW(),
                    last_max_date = COALESCE(EXCLUDED.last_max_date, sync_metadata.last_max_date),
                    last_user = EXCLUDED.last_user
                """
                ),
                {
                    "t": target,
                    "m": max_date_in_batch.to_pydatetime()
                    if max_date_in_batch is not None
                    else None,
                    "u": user_email,
                },
            )

    # 6. Insert import_log row
    finished = datetime.utcnow()
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                INSERT INTO import_log
                (started_at, finished_at, source_file, table_name, sync_strategy,
                 rows_read, rows_inserted, rows_updated, rows_skipped, mode, user_email)
                VALUES (:s, :f, :src, :t, :strat, :rr, :ri, :ru, :rs, :m, :u)
                """
                ),
                {
                    "s": started,
                    "f": finished,
                    "src": accdb_path.name,
                    "t": target,
                    "strat": strategy,
                    "rr": rows_read_total,
                    "ri": n_new if mode == "apply" else 0,
                    "ru": n_updated if mode == "apply" else 0,
                    "rs": result["errors"],
                    "m": mode,
                    "u": user_email,
                },
            )
    except Exception as e:
        log(f"  ⚠️  import_log echec: {e}")

    return result


# ============================================
# MAIN
# ============================================


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--accdb", required=True, help="Chemin vers le fichier .accdb")
    ap.add_argument(
        "--mode",
        choices=("preview", "apply"),
        required=True,
        help="preview = dry-run, apply = effectue les UPSERT",
    )
    ap.add_argument("--user", default=None, help="Email de l'utilisateur (pour les logs)")
    args = ap.parse_args()

    output: Dict[str, Any] = {
        "ok": False,
        "mode": args.mode,
        "started_at": datetime.utcnow().isoformat(),
        "tables": [],
        "errors": [],
    }

    try:
        check_mdbtools()
        accdb = Path(args.accdb)
        if not accdb.exists():
            raise FileNotFoundError(f"Fichier introuvable: {accdb}")

        # Validation : vérifier que les tables attendues existent
        access_tables = list_access_tables(accdb)
        expected = [c["access_table"] for c in TABLES_CONFIG]
        missing = [t for t in expected if t not in access_tables]
        if missing:
            output["errors"].append(
                {
                    "stage": "validation",
                    "message": f"Tables manquantes dans le .accdb: {missing}",
                }
            )
            print(json.dumps(output, default=str))
            return 2
        output["validation"] = {"tables_found": len(expected), "missing": []}

        engine = create_engine(DATABASE_URL, pool_pre_ping=True)

        for cfg in TABLES_CONFIG:
            try:
                stats = process_table(engine, accdb, cfg, args.mode, args.user)
                output["tables"].append(stats)
            except Exception as e:
                log(f"⛔ {cfg['access_table']} -> {e}")
                output["errors"].append(
                    {
                        "stage": cfg["access_table"],
                        "message": str(e),
                        "trace": traceback.format_exc(),
                    }
                )

        output["finished_at"] = datetime.utcnow().isoformat()
        # Totaux
        output["totals"] = {
            "new": sum(t["new"] for t in output["tables"]),
            "updated": sum(t["updated"] for t in output["tables"]),
            "errors": sum(t["errors"] for t in output["tables"]),
        }
        output["ok"] = len(output["errors"]) == 0

        print(json.dumps(output, default=str, ensure_ascii=False))
        return 0 if output["ok"] else 1

    except Exception as e:
        output["errors"].append(
            {"stage": "main", "message": str(e), "trace": traceback.format_exc()}
        )
        print(json.dumps(output, default=str, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
