#!/usr/bin/env python3
"""
Migration Excel → Supabase PostgreSQL
Multirex DMS

Usage:
    python migrate_to_supabase.py

Prérequis:
    pip install pandas openpyxl xlrd psycopg2-binary sqlalchemy
"""

import os
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# ============================================
# CONFIGURATION
# ============================================

# URL de connexion Supabase (à modifier)
# Format: postgresql://user:password@host:port/database
SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "postgresql://postgres.ybaqkghlphxvkjmvtcly:1QoAroELqbzQDh9v@aws-1-eu-west-1.pooler.supabase.com:6543/postgres"
)
# Dossier contenant les fichiers Excel
EXCEL_DIR = Path("./data")  # À ajuster selon votre structure

# ============================================
# MAPPING FICHIERS → TABLES
# ============================================

# Ordre d'import (respecte les dépendances de clés étrangères)
IMPORT_ORDER = [
    # 1. Tables de référence (pas de FK)
    ("tbl_Affectations.xlsx", "tbl_affectations", {
        "N_Affectation": "n_affectation",
        "Nom Affectation": "nom_affectation",
        "SélectionAffectation": "selection_affectation",
    }),
    ("tbl_Emplacements.xlsx", "tbl_emplacements", {
        "IDEmplacement": "id_emplacement",
        "NomEmplacement": "nom_emplacement",
        "SélectionEmplacement": "selection_emplacement",
    }),
    ("tbl_Energie.xlsx", "tbl_energie", {
        "N_Energie": "n_energie",
        "Nom Energie": "nom_energie",
        "Nom Energie Anglais": "nom_energie_anglais",
    }),
    ("tbl_Etats_divers.xlsx", "tbl_etats_divers", {
        "N_Etat": "n_etat",
        "Etat": "etat",
        "EtatAnglais": "etat_anglais",
        "SélectionEtat": "selection_etat",
        "Abréviation": "abreviation",
    }),
    ("tbl_Marques.xlsx", "tbl_marques", {
        "N_Marque": "n_marque",
        "Nom Marque": "nom_marque",
        "SélectionMarque": "selection_marque",
    }),
    ("tbl_Pays.xlsx", "tbl_pays", {
        "N_Pays": "n_pays",
        "Nom Pays": "nom_pays",
        "SélectionPays": "selection_pays",
    }),
    
    # ============================================
    # 🆕 AJOUT: tbl_Types_moteurs (référencé par tbl_moteurs via n_type_moteur)
    # ============================================
    ("tbl_Types_moteurs.xlsx", "tbl_types_moteurs", {
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
    }),
    
    # 2. Tables avec FK simples
    ("tbl_Fournisseurs.xlsx", "tbl_fournisseurs", {
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
    }),
    ("tbl_Clients.xlsx", "tbl_clients", {
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
    }),
    ("tbl_RECEPTIONS.xlsx", "tbl_receptions", {
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
    }),
    ("tbl_EXPEDITIONS.xlsx", "tbl_expeditions", {
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
    }),
    
    # 3. Tables principales
    ("tbl_MOTEURS.xlsx", "tbl_moteurs", {
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
    }),
    ("tbl_BOITES.xlsx", "tbl_boites", {
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
    }),
    
    # 4. Tables de liaison
    ("tbl_EXPEDITIONS_moteurs.xlsx", "tbl_expeditions_moteurs", {
        "N_Expédition": "n_expedition",
        "N_moteur": "n_moteur",
        "PrixVenteMoteur": "prix_vente_moteur",
        "DateValidation": "date_validation",
    }),
    ("tbl_EXPEDITIONS_boîtes.xlsx", "tbl_expeditions_boites", {
        "N_Expédition": "n_expedition",
        "N_BV": "n_bv",
        "PrixVenteBV": "prix_vente_bv",
        "DateValidation": "date_validation",
    }),
    ("tbl_FACTURES.xlsx", "tbl_factures", {
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
    }),
    ("tbl_PIECES.xlsx", "tbl_pieces", {
        "N_réception": "n_reception",
        "Qté": "qte",
        "N_TypePièce": "n_type_piece",
        "ModèlePièce": "modele_piece",
        "PUpièce": "pu_piece",
        "TotalHAPièce": "total_ha_piece",
    }),
]


# ============================================
# 🆕 SQL POUR CRÉER LA TABLE tbl_types_moteurs
# ============================================

CREATE_TYPES_MOTEURS_SQL = """
-- Table des types de moteurs (référentiel)
CREATE TABLE IF NOT EXISTS tbl_types_moteurs (
    n_type_moteur INTEGER PRIMARY KEY,
    n_marque INTEGER,
    avec_specif BOOLEAN,
    nom_type_moteur VARCHAR(255),
    modele_type_moteur TEXT,
    n_energie INTEGER,
    obs_energie TEXT,
    annee VARCHAR(50),
    particularite_type_moteur TEXT,
    equivalence_type_moteur TEXT,
    prix_vente_mbv NUMERIC(12, 2),
    prix_vente_m_seul NUMERIC(12, 2),
    hs_code VARCHAR(50),
    prix_achat_base_type_mot NUMERIC(12, 2)
);

-- Index pour les jointures fréquentes
CREATE INDEX IF NOT EXISTS idx_types_moteurs_marque ON tbl_types_moteurs(n_marque);
CREATE INDEX IF NOT EXISTS idx_types_moteurs_energie ON tbl_types_moteurs(n_energie);
CREATE INDEX IF NOT EXISTS idx_types_moteurs_nom ON tbl_types_moteurs(nom_type_moteur);

-- Commentaire
COMMENT ON TABLE tbl_types_moteurs IS 'Table de référence des types de moteurs avec leurs caractéristiques';
"""


# ============================================
# 🆕 SQL POUR METTRE À JOUR LA VUE v_moteurs_dispo
# ============================================

UPDATE_VIEW_MOTEURS_DISPO_SQL = """
-- Supprime l'ancienne vue si elle existe
DROP VIEW IF EXISTS v_moteurs_dispo;

-- Recrée la vue avec les infos du type moteur
CREATE VIEW v_moteurs_dispo AS
SELECT
    m.*,
    -- Infos du type moteur
    tm.nom_type_moteur AS type_nom,
    tm.modele_type_moteur AS type_modele,
    tm.annee AS type_annee,
    tm.particularite_type_moteur AS type_particularite,
    tm.equivalence_type_moteur AS type_equivalence,
    tm.prix_vente_mbv AS type_prix_vente_mbv,
    tm.prix_vente_m_seul AS type_prix_vente_seul,
    tm.hs_code AS type_hs_code,
    tm.prix_achat_base_type_mot AS type_prix_achat_base,
    -- Infos marque
    ma.nom_marque AS marque,
    -- Infos énergie
    en.nom_energie AS energie,
    -- Calcul disponibilité
    CASE 
        WHEN m.n_expedition IS NULL 
         AND (m.archiver IS NULL OR m.archiver = FALSE)
         AND m.date_sortie IS NULL
        THEN 1 
        ELSE 0 
    END AS est_disponible
FROM tbl_moteurs m
LEFT JOIN tbl_types_moteurs tm ON tm.n_type_moteur = m.n_type_moteur
LEFT JOIN tbl_marques ma ON ma.n_marque = tm.n_marque
LEFT JOIN tbl_energie en ON en.n_energie = tm.n_energie;

-- Commentaire
COMMENT ON VIEW v_moteurs_dispo IS 'Vue enrichie des moteurs avec type, marque, énergie et statut de disponibilité';
"""


# ============================================
# FONCTIONS
# ============================================

def clean_dataframe(df: pd.DataFrame, column_mapping: dict) -> pd.DataFrame:
    """Nettoie et renomme les colonnes d'un DataFrame."""
    
    # Ne garder que les colonnes qui existent dans le mapping
    existing_cols = [c for c in column_mapping.keys() if c in df.columns]
    df = df[existing_cols].copy()
    
    # Renommer les colonnes
    rename_map = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    
    # Nettoyer les valeurs
    for col in df.columns:
        # Convertir les NaN en None pour PostgreSQL
        df[col] = df[col].where(pd.notna(df[col]), None)
        
        # Nettoyer les chaînes
        if df[col].dtype == 'object':
            df[col] = df[col].apply(lambda x: str(x).strip() if pd.notna(x) and x is not None else None)
            # Remplacer les chaînes vides par None
            df[col] = df[col].apply(lambda x: None if x == '' or x == 'nan' or x == 'None' else x)
    
    return df


def import_excel_to_postgres(
    engine,
    excel_path: Path,
    table_name: str,
    column_mapping: dict,
    chunk_size: int = 5000
) -> int:
    """Importe un fichier Excel vers PostgreSQL."""
    
    if not excel_path.exists():
        print(f"  ⚠️  Fichier non trouvé: {excel_path}")
        return 0
    
    try:
        # Lire le fichier Excel
        df = pd.read_excel(excel_path, engine="openpyxl")
        
        if df.empty:
            print(f"  ⚠️  Fichier vide: {excel_path}")
            return 0
        
        # Nettoyer les données
        df = clean_dataframe(df, column_mapping)
        
        # Vider la table existante
        with engine.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
            conn.commit()
        
        # Insérer par chunks
        total_rows = 0
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i+chunk_size]
            chunk.to_sql(
                table_name,
                engine,
                if_exists='append',
                index=False,
                method='multi'
            )
            total_rows += len(chunk)
            print(f"    → {total_rows:,} / {len(df):,} lignes...", end='\r')
        
        print(f"  ✅ {table_name}: {total_rows:,} lignes importées")
        return total_rows
        
    except Exception as e:
        print(f"  ❌ Erreur {table_name}: {e}")
        return 0


def run_schema(engine, schema_path: Path):
    """Exécute le script de création du schéma."""
    
    print("\n📋 Création du schéma...")
    
    if not schema_path.exists():
        print(f"  ❌ Fichier schéma non trouvé: {schema_path}")
        return False
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Séparer les statements
        statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
        
        with engine.connect() as conn:
            for stmt in statements:
                if stmt and not stmt.startswith('--'):
                    try:
                        conn.execute(text(stmt))
                    except SQLAlchemyError as e:
                        # Ignorer certaines erreurs (DROP IF NOT EXISTS, etc.)
                        if "does not exist" not in str(e):
                            print(f"  ⚠️  {str(e)[:100]}")
            conn.commit()
        
        print("  ✅ Schéma créé avec succès")
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur schéma: {e}")
        return False


def create_types_moteurs_table(engine):
    """🆕 Crée la table tbl_types_moteurs si elle n'existe pas."""
    
    print("\n📋 Création de la table tbl_types_moteurs...")
    
    try:
        with engine.connect() as conn:
            # Séparer les statements
            statements = [s.strip() for s in CREATE_TYPES_MOTEURS_SQL.split(';') if s.strip()]
            
            for stmt in statements:
                if stmt and not stmt.startswith('--'):
                    try:
                        conn.execute(text(stmt))
                    except SQLAlchemyError as e:
                        if "already exists" not in str(e).lower():
                            print(f"  ⚠️  {str(e)[:100]}")
            conn.commit()
        
        print("  ✅ Table tbl_types_moteurs prête")
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur création table: {e}")
        return False


def update_view_moteurs_dispo(engine):
    """🆕 Met à jour la vue v_moteurs_dispo avec les infos du type moteur."""
    
    print("\n📋 Mise à jour de la vue v_moteurs_dispo...")
    
    try:
        with engine.connect() as conn:
            # Séparer les statements
            statements = [s.strip() for s in UPDATE_VIEW_MOTEURS_DISPO_SQL.split(';') if s.strip()]
            
            for stmt in statements:
                if stmt and not stmt.startswith('--'):
                    try:
                        conn.execute(text(stmt))
                    except SQLAlchemyError as e:
                        print(f"  ⚠️  {str(e)[:100]}")
            conn.commit()
        
        print("  ✅ Vue v_moteurs_dispo mise à jour")
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur vue: {e}")
        return False


# ============================================
# 🆕 IMPORT PIECES DETACHEES (4 fichiers Excel stock)
# ============================================

_STOCK_HEADERS = ("STOCK", "QUANTITE", "QUANTITES", "QTE", "QTY")


def _find_stock_col(df, max_header_rows: int = 3) -> int | None:
    """Scan header rows for STOCK/QUANTITE. Returns the LAST match (rightmost column) to handle
    sheets with both an "initial stock" and a "final stock" column (ex: démarreurs)."""
    found = None
    for r in range(min(max_header_rows, len(df))):
        for c, v in enumerate(df.iloc[r]):
            if pd.notna(v) and isinstance(v, str) and v.strip().upper() in _STOCK_HEADERS:
                found = c
    return found


def _parse_compressors(excel_dir: Path) -> tuple[list[dict], list[dict]]:
    """Parse Stock COMPRESSEURS CLIM.xlsx → stock + mouvements."""
    path = excel_dir / "Stock COMPRESSEURS CLIM.xlsx"
    stock_rows, mvt_rows = [], []
    if not path.exists():
        print(f"  ⚠️  Fichier non trouvé: {path}")
        return stock_rows, mvt_rows
    try:
        raw = pd.read_excel(path, sheet_name="Feuil1", header=None, engine="openpyxl")
        stock_col = _find_stock_col(raw)
        # Mouvements occupent cols [2 .. stock_col-1] si stock_col trouvé, sinon cols [2 .. last-1]
        mvt_last = stock_col if stock_col is not None else raw.shape[1] - 1
        dates_row = raw.iloc[1, 2:mvt_last] if len(raw) > 1 else pd.Series()
        clients_row = raw.iloc[2, 2:mvt_last] if len(raw) > 2 else pd.Series()
        for i in range(4, len(raw)):
            brand = str(raw.iloc[i, 0]).strip() if pd.notna(raw.iloc[i, 0]) else ""
            ref = str(raw.iloc[i, 1]).strip() if pd.notna(raw.iloc[i, 1]) else ""
            qty = _safe_int(raw.iloc[i, stock_col]) if stock_col is not None else 0
            if ref and ref.upper() not in ("NAN", ""):
                stock_rows.append({"categorie": "Compresseur Clim", "marque": brand, "reference": ref, "modele": "", "ref_constructeur": "", "observations": "", "stock": qty})
                # Mouvements
                for j in range(2, mvt_last):
                    val = raw.iloc[i, j]
                    if pd.notna(val) and val != 0:
                        try:
                            val = int(val)
                        except (ValueError, TypeError):
                            continue
                        dt = dates_row.iloc[j - 2] if (j - 2) < len(dates_row) else None
                        cl = str(clients_row.iloc[j - 2]).strip() if (j - 2) < len(clients_row) and pd.notna(clients_row.iloc[j - 2]) else ""
                        dt_parsed = pd.to_datetime(dt, errors="coerce")
                        if pd.notna(dt_parsed):
                            mvt_rows.append({"categorie": "Compresseur Clim", "reference": ref, "date_mouvement": dt_parsed, "quantite": val, "client": cl})
        print(f"  ✅ Compresseurs: {len(stock_rows)} refs, {len(mvt_rows)} mouvements (stock col={stock_col})")
    except Exception as e:
        print(f"  ❌ Erreur compresseurs: {e}")
    return stock_rows, mvt_rows


def _parse_steering(excel_dir: Path) -> tuple[list[dict], list[dict]]:
    """Parse Stock CREM-PDA-COLONNES.xlsx → stock (mouvements non extractibles)."""
    path = excel_dir / "Stock CREM-PDA-COLONNES.xlsx"
    stock_rows, mvt_rows = [], []
    if not path.exists():
        print(f"  ⚠️  Fichier non trouvé: {path}")
        return stock_rows, mvt_rows
    try:
        xls = pd.ExcelFile(path, engine="openpyxl")
    except Exception as e:
        print(f"  ❌ Erreur CREM-PDA: {e}")
        return stock_rows, mvt_rows

    # CREMAILLERES - colonnes fixes: Pieces | Type | Marque | Modele | (vide) | REF | QUANTITE
    try:
        raw = pd.read_excel(xls, sheet_name="CREMAILLERES - RACKS", header=None)
        for i in range(1, len(raw)):
            ref = str(raw.iloc[i, 5]).strip() if pd.notna(raw.iloc[i, 5]) else ""
            brand = str(raw.iloc[i, 2]).strip() if pd.notna(raw.iloc[i, 2]) else ""
            model = str(raw.iloc[i, 3]).strip() if pd.notna(raw.iloc[i, 3]) else ""
            qty = _safe_int(raw.iloc[i, 6])
            if ref and ref.upper() not in ("NAN", ""):
                stock_rows.append({"categorie": "Cremaillere", "marque": brand, "reference": ref, "modele": model, "ref_constructeur": "", "observations": "", "stock": qty})
    except Exception:
        pass

    # EHPS Pumps - détection colonne stock par header
    for sn in xls.sheet_names:
        if "EHPS" in sn.upper() or "Pump" in sn:
            try:
                raw = pd.read_excel(xls, sheet_name=sn, header=None)
                stock_col = _find_stock_col(raw)
                for i in range(4, len(raw)):
                    brand = str(raw.iloc[i, 0]).strip() if pd.notna(raw.iloc[i, 0]) else ""
                    model = str(raw.iloc[i, 1]).strip() if pd.notna(raw.iloc[i, 1]) else ""
                    ref = str(raw.iloc[i, 2]).strip() if pd.notna(raw.iloc[i, 2]) else ""
                    qty = _safe_int(raw.iloc[i, stock_col]) if stock_col is not None else 0
                    if ref and ref.upper() not in ("NAN", ""):
                        stock_rows.append({"categorie": "Pompe EHPS", "marque": brand, "reference": ref, "modele": model, "ref_constructeur": "", "observations": "", "stock": qty})
            except Exception:
                pass

    # Colonne Electrique - détection colonne stock par header
    for sn in xls.sheet_names:
        if "colonne" in sn.lower() or "column" in sn.lower():
            try:
                raw = pd.read_excel(xls, sheet_name=sn, header=None)
                stock_col = _find_stock_col(raw)
                for i in range(4, len(raw)):
                    brand = str(raw.iloc[i, 0]).strip() if pd.notna(raw.iloc[i, 0]) else ""
                    model = str(raw.iloc[i, 1]).strip() if pd.notna(raw.iloc[i, 1]) else ""
                    ref = str(raw.iloc[i, 2]).strip() if pd.notna(raw.iloc[i, 2]) else ""
                    qty = _safe_int(raw.iloc[i, stock_col]) if stock_col is not None else 0
                    if ref and ref.upper() not in ("NAN", ""):
                        stock_rows.append({"categorie": "Colonne Electrique", "marque": brand, "reference": ref, "modele": model, "ref_constructeur": "", "observations": "", "stock": qty})
            except Exception:
                pass

    print(f"  ✅ CREM-PDA-Colonnes: {len(stock_rows)} refs")
    return stock_rows, mvt_rows


def _safe_int(val) -> int:
    """Safely convert a value to int, returning 0 on failure."""
    if pd.isna(val):
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def _parse_starters(excel_dir: Path) -> tuple[list[dict], list[dict]]:
    """Parse Stock DEMARREURS.xls → stock + mouvements."""
    path = excel_dir / "Stock DEMARREURS.xls"
    stock_rows, mvt_rows = [], []
    if not path.exists():
        print(f"  ⚠️  Fichier non trouvé: {path}")
        return stock_rows, mvt_rows
    try:
        raw = pd.read_excel(path, header=None, engine="xlrd")
        stock_col = _find_stock_col(raw)
        mvt_last = stock_col if stock_col is not None else raw.shape[1] - 1
        dates_row = raw.iloc[0, 3:mvt_last] if len(raw) > 0 else pd.Series()
        clients_row = raw.iloc[1, 3:mvt_last] if len(raw) > 1 else pd.Series()
        for i in range(2, len(raw)):
            ref = str(raw.iloc[i, 1]).strip() if pd.notna(raw.iloc[i, 1]) else ""
            qty = _safe_int(raw.iloc[i, stock_col]) if stock_col is not None else 0
            if ref and ref.upper() not in ("NAN", ""):
                stock_rows.append({"categorie": "Demarreur", "marque": "", "reference": ref, "modele": "", "ref_constructeur": "", "observations": "", "stock": qty})
                # Mouvements
                for j in range(3, mvt_last):
                    val = _safe_int(raw.iloc[i, j])
                    if val != 0:
                        dt = dates_row.iloc[j - 3] if (j - 3) < len(dates_row) else None
                        cl = str(clients_row.iloc[j - 3]).strip() if (j - 3) < len(clients_row) and pd.notna(clients_row.iloc[j - 3]) else ""
                        dt_parsed = pd.to_datetime(dt, errors="coerce")
                        if pd.notna(dt_parsed):
                            mvt_rows.append({"categorie": "Demarreur", "reference": ref, "date_mouvement": dt_parsed, "quantite": val, "client": cl})
        print(f"  ✅ Demarreurs: {len(stock_rows)} refs, {len(mvt_rows)} mouvements (stock col={stock_col})")
    except Exception as e:
        print(f"  ❌ Erreur demarreurs: {e}")
    return stock_rows, mvt_rows


def _parse_calculators(excel_dir: Path) -> tuple[list[dict], list[dict]]:
    """Parse Stock CALC-BSI-BSM-ABS-COM.xlsx → stock."""
    path = excel_dir / "Stock CALC-BSI-BSM-ABS-COM.xlsx"
    stock_rows, mvt_rows = [], []
    if not path.exists():
        print(f"  ⚠️  Fichier non trouvé: {path}")
        return stock_rows, mvt_rows
    try:
        xls = pd.ExcelFile(path, engine="openpyxl")
    except Exception as e:
        print(f"  ❌ Erreur CALC: {e}")
        return stock_rows, mvt_rows

    # Calculateur : Marque | REF | Type-code (E78/E83) | dates... | Stock
    try:
        raw = pd.read_excel(xls, sheet_name="Calculateur", header=None)
        stock_col = _find_stock_col(raw)
        mvt_last = stock_col if stock_col is not None else raw.shape[1] - 1
        dates_row = raw.iloc[0, 3:mvt_last] if len(raw) > 0 else pd.Series()
        clients_row = raw.iloc[1, 3:mvt_last] if len(raw) > 1 else pd.Series()
        for i in range(3, len(raw)):
            brand = str(raw.iloc[i, 0]).strip() if pd.notna(raw.iloc[i, 0]) else ""
            ref = str(raw.iloc[i, 1]).strip() if pd.notna(raw.iloc[i, 1]) else ""
            type_code = str(raw.iloc[i, 2]).strip() if pd.notna(raw.iloc[i, 2]) else ""
            qty = _safe_int(raw.iloc[i, stock_col]) if stock_col is not None else 0
            if ref and ref.upper() not in ("NAN", ""):
                stock_rows.append({"categorie": "Calculateur", "marque": brand, "reference": ref, "modele": type_code, "ref_constructeur": "", "observations": "", "stock": qty})
                for j in range(3, mvt_last):
                    val = _safe_int(raw.iloc[i, j])
                    if val != 0:
                        dt = dates_row.iloc[j - 3] if (j - 3) < len(dates_row) else None
                        cl = str(clients_row.iloc[j - 3]).strip() if (j - 3) < len(clients_row) and pd.notna(clients_row.iloc[j - 3]) else ""
                        dt_parsed = pd.to_datetime(dt, errors="coerce")
                        if pd.notna(dt_parsed):
                            mvt_rows.append({"categorie": "Calculateur", "reference": ref, "date_mouvement": dt_parsed, "quantite": val, "client": cl})
    except Exception as e:
        print(f"  ⚠️  Calculateur: {e}")

    # BSI BSM : Marque | REF CONSTRUCTEUR | REF | REF MARQUE | dates... | Stock
    try:
        raw = pd.read_excel(xls, sheet_name="BSI BSM", header=None)
        stock_col = _find_stock_col(raw)
        mvt_last = stock_col if stock_col is not None else raw.shape[1] - 1
        dates_row = raw.iloc[2, 4:mvt_last] if len(raw) > 2 else pd.Series()
        clients_row = raw.iloc[3, 4:mvt_last] if len(raw) > 3 else pd.Series()
        for i in range(4, len(raw)):
            brand = str(raw.iloc[i, 0]).strip() if pd.notna(raw.iloc[i, 0]) else ""
            ref_constr = str(raw.iloc[i, 1]).strip() if pd.notna(raw.iloc[i, 1]) else ""
            ref = str(raw.iloc[i, 2]).strip() if pd.notna(raw.iloc[i, 2]) else ""
            qty = _safe_int(raw.iloc[i, stock_col]) if stock_col is not None else 0
            if ref and ref.upper() not in ("NAN", ""):
                stock_rows.append({"categorie": "BSI/BSM", "marque": brand, "reference": ref, "modele": "", "ref_constructeur": ref_constr, "observations": "", "stock": qty})
                for j in range(4, mvt_last):
                    val = _safe_int(raw.iloc[i, j])
                    if val != 0:
                        dt = dates_row.iloc[j - 4] if (j - 4) < len(dates_row) else None
                        cl = str(clients_row.iloc[j - 4]).strip() if (j - 4) < len(clients_row) and pd.notna(clients_row.iloc[j - 4]) else ""
                        dt_parsed = pd.to_datetime(dt, errors="coerce")
                        if pd.notna(dt_parsed):
                            mvt_rows.append({"categorie": "BSI/BSM", "reference": ref, "date_mouvement": dt_parsed, "quantite": val, "client": cl})
    except Exception as e:
        print(f"  ⚠️  BSI BSM: {e}")

    # ABS : Marque | REF | REF CONSTRUCTEUR | OBSERVATIONS | dates... | Stock
    try:
        raw = pd.read_excel(xls, sheet_name="ABS", header=None)
        stock_col = _find_stock_col(raw)
        mvt_last = stock_col if stock_col is not None else raw.shape[1] - 1
        dates_row = raw.iloc[0, 4:mvt_last] if len(raw) > 0 else pd.Series()
        clients_row = raw.iloc[1, 4:mvt_last] if len(raw) > 1 else pd.Series()
        for i in range(2, len(raw)):
            brand = str(raw.iloc[i, 0]).strip() if pd.notna(raw.iloc[i, 0]) else ""
            ref = str(raw.iloc[i, 1]).strip() if pd.notna(raw.iloc[i, 1]) else ""
            ref_constr = str(raw.iloc[i, 2]).strip() if pd.notna(raw.iloc[i, 2]) else ""
            obs = str(raw.iloc[i, 3]).strip() if pd.notna(raw.iloc[i, 3]) else ""
            qty = _safe_int(raw.iloc[i, stock_col]) if stock_col is not None else 0
            if ref and ref.upper() not in ("NAN", ""):
                stock_rows.append({"categorie": "ABS", "marque": brand, "reference": ref, "modele": "", "ref_constructeur": ref_constr, "observations": obs, "stock": qty})
                for j in range(4, mvt_last):
                    val = _safe_int(raw.iloc[i, j])
                    if val != 0:
                        dt = dates_row.iloc[j - 4] if (j - 4) < len(dates_row) else None
                        cl = str(clients_row.iloc[j - 4]).strip() if (j - 4) < len(clients_row) and pd.notna(clients_row.iloc[j - 4]) else ""
                        dt_parsed = pd.to_datetime(dt, errors="coerce")
                        if pd.notna(dt_parsed):
                            mvt_rows.append({"categorie": "ABS", "reference": ref, "date_mouvement": dt_parsed, "quantite": val, "client": cl})
    except Exception as e:
        print(f"  ⚠️  ABS: {e}")

    # COM 2000
    for sn in xls.sheet_names:
        if "COM" in sn.upper() and "2000" in sn:
            try:
                raw = pd.read_excel(xls, sheet_name=sn, header=None)
                stock_col = _find_stock_col(raw)
                for i in range(4, len(raw)):
                    brand = str(raw.iloc[i, 0]).strip() if pd.notna(raw.iloc[i, 0]) else ""
                    model = str(raw.iloc[i, 1]).strip() if pd.notna(raw.iloc[i, 1]) else ""
                    ref = str(raw.iloc[i, 2]).strip() if pd.notna(raw.iloc[i, 2]) else ""
                    qty = _safe_int(raw.iloc[i, stock_col]) if stock_col is not None else 0
                    if ref and ref.upper() not in ("NAN", ""):
                        stock_rows.append({"categorie": "COM 2000", "marque": brand, "reference": ref, "modele": model, "ref_constructeur": "", "observations": "", "stock": qty})
            except Exception:
                pass

    # Boitier Papillon
    for sn in xls.sheet_names:
        if "papillon" in sn.lower():
            try:
                raw = pd.read_excel(xls, sheet_name=sn, header=None)
                stock_col = _find_stock_col(raw)
                for i in range(3, len(raw)):
                    brand = str(raw.iloc[i, 0]).strip() if pd.notna(raw.iloc[i, 0]) else ""
                    ref = str(raw.iloc[i, 1]).strip() if pd.notna(raw.iloc[i, 1]) else ""
                    qty = _safe_int(raw.iloc[i, stock_col]) if stock_col is not None else 0
                    if ref and ref.upper() not in ("NAN", ""):
                        stock_rows.append({"categorie": "Boitier Papillon", "marque": brand, "reference": ref, "modele": "", "ref_constructeur": "", "observations": "", "stock": qty})
            except Exception:
                pass

    print(f"  ✅ CALC-BSI-ABS-COM: {len(stock_rows)} refs, {len(mvt_rows)} mouvements")
    return stock_rows, mvt_rows


CREATE_PIECES_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS tbl_pieces_detachees (
    id SERIAL PRIMARY KEY,
    categorie TEXT NOT NULL,
    marque TEXT DEFAULT '',
    reference TEXT NOT NULL,
    modele TEXT DEFAULT '',
    ref_constructeur TEXT DEFAULT '',
    observations TEXT DEFAULT '',
    stock INTEGER DEFAULT 0,
    date_import TIMESTAMP DEFAULT NOW()
);
ALTER TABLE tbl_pieces_detachees ADD COLUMN IF NOT EXISTS ref_constructeur TEXT DEFAULT '';
ALTER TABLE tbl_pieces_detachees ADD COLUMN IF NOT EXISTS observations TEXT DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_pieces_det_categorie ON tbl_pieces_detachees(categorie);
CREATE INDEX IF NOT EXISTS idx_pieces_det_reference ON tbl_pieces_detachees(reference);
CREATE INDEX IF NOT EXISTS idx_pieces_det_marque ON tbl_pieces_detachees(marque);
CREATE INDEX IF NOT EXISTS idx_pieces_det_refc ON tbl_pieces_detachees(ref_constructeur);

CREATE TABLE IF NOT EXISTS tbl_pieces_mouvements (
    id SERIAL PRIMARY KEY,
    categorie TEXT NOT NULL,
    reference TEXT NOT NULL,
    date_mouvement TIMESTAMP,
    quantite INTEGER DEFAULT 0,
    client TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_pieces_mvt_ref ON tbl_pieces_mouvements(reference);
CREATE INDEX IF NOT EXISTS idx_pieces_mvt_cat ON tbl_pieces_mouvements(categorie);
CREATE INDEX IF NOT EXISTS idx_pieces_mvt_date ON tbl_pieces_mouvements(date_mouvement);
"""


def import_pieces_detachees(engine, excel_dir: Path) -> int:
    """Import all 4 stock Excel files into tbl_pieces_detachees + tbl_pieces_mouvements."""
    print("\n📦 Import des pièces détachées (4 fichiers Excel)...")

    # Créer les tables si elles n'existent pas
    print("  📋 Création des tables pièces détachées...")
    try:
        with engine.connect() as conn:
            for stmt in [s.strip() for s in CREATE_PIECES_TABLES_SQL.split(";") if s.strip()]:
                if stmt and not stmt.startswith("--"):
                    conn.execute(text(stmt))
            conn.commit()
        print("  ✅ Tables prêtes")
    except Exception as e:
        print(f"  ⚠️  Erreur création tables: {e}")

    all_stock = []
    all_mvts = []

    for parser in [_parse_compressors, _parse_steering, _parse_starters, _parse_calculators]:
        s, m = parser(excel_dir)
        all_stock.extend(s)
        all_mvts.extend(m)

    total = 0

    # Insert stock
    if all_stock:
        df_stock = pd.DataFrame(all_stock)
        df_stock["stock"] = pd.to_numeric(df_stock["stock"], errors="coerce").fillna(0).astype(int)
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE tbl_pieces_detachees RESTART IDENTITY CASCADE"))
            conn.commit()
        df_stock.to_sql("tbl_pieces_detachees", engine, if_exists="append", index=False, method="multi")
        total += len(df_stock)
        print(f"  ✅ tbl_pieces_detachees: {len(df_stock):,} références importées")

    # Insert mouvements
    if all_mvts:
        df_mvts = pd.DataFrame(all_mvts)
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE tbl_pieces_mouvements RESTART IDENTITY CASCADE"))
            conn.commit()
        # Insert in chunks to avoid memory issues
        chunk_size = 5000
        for i in range(0, len(df_mvts), chunk_size):
            chunk = df_mvts.iloc[i:i + chunk_size]
            chunk.to_sql("tbl_pieces_mouvements", engine, if_exists="append", index=False, method="multi")
        total += len(df_mvts)
        print(f"  ✅ tbl_pieces_mouvements: {len(df_mvts):,} mouvements importés")
    else:
        print("  ℹ️  Aucun mouvement extrait (normal pour certains fichiers)")

    return total


def main():
    print("=" * 60)
    print("🚀 Migration Excel → Supabase PostgreSQL")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Dossier Excel: {EXCEL_DIR}")
    print(f"🔗 Supabase: {SUPABASE_URL.split('@')[1] if '@' in SUPABASE_URL else '***'}")
    print()
    
    # Connexion
    print("🔌 Connexion à Supabase...")
    try:
        engine = create_engine(SUPABASE_URL, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT NOW()"))
            print(f"  ✅ Connecté ! Heure serveur: {result.fetchone()[0]}")
    except Exception as e:
        print(f"  ❌ Erreur de connexion: {e}")
        sys.exit(1)
    
    # Schéma principal
    schema_path = Path(__file__).parent / "supabase_schema.sql"
    if schema_path.exists():
        run_schema(engine, schema_path)
    else:
        print(f"  ⚠️  Schéma non trouvé: {schema_path}")
        print("     Assurez-vous d'avoir exécuté le schéma manuellement dans Supabase")
    
    # 🆕 Créer la table tbl_types_moteurs
    create_types_moteurs_table(engine)
    
    # Import des données
    print("\n📦 Import des données...")
    total_imported = 0
    
    for excel_file, table_name, column_mapping in IMPORT_ORDER:
        excel_path = EXCEL_DIR / excel_file
        count = import_excel_to_postgres(engine, excel_path, table_name, column_mapping)
        total_imported += count
    
    # 🆕 Mettre à jour la vue après import
    update_view_moteurs_dispo(engine)

    # 🆕 Import des pièces détachées (4 fichiers Excel stock)
    pieces_count = import_pieces_detachees(engine, EXCEL_DIR)
    total_imported += pieces_count

    # Résumé
    print("\n" + "=" * 60)
    print(f"✅ Migration terminée !")
    print(f"📊 Total: {total_imported:,} lignes importées")
    print("=" * 60)
    
    # Vérification
    print("\n🔍 Vérification des vues...")
    try:
        with engine.connect() as conn:
            # Test v_moteurs_dispo
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) AS total,
                    SUM(CASE WHEN est_disponible = 1 THEN 1 ELSE 0 END) AS dispo
                FROM v_moteurs_dispo
            """))
            row = result.fetchone()
            print(f"  📦 v_moteurs_dispo: {row[0]:,} moteurs, {row[1]:,} disponibles")
            
            # 🆕 Test tbl_types_moteurs
            result = conn.execute(text("""
                SELECT COUNT(*) FROM tbl_types_moteurs
            """))
            row = result.fetchone()
            print(f"  📦 tbl_types_moteurs: {row[0]:,} types de moteurs")
            
            # 🆕 Test jointure type moteur
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM v_moteurs_dispo 
                WHERE type_nom IS NOT NULL
            """))
            row = result.fetchone()
            print(f"  📦 Moteurs avec type renseigné: {row[0]:,}")
            
            # Test v_boites_dispo
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) AS total,
                    SUM(CASE WHEN est_disponible = 1 THEN 1 ELSE 0 END) AS dispo
                FROM v_boites_dispo
            """))
            row = result.fetchone()
            print(f"  📦 v_boites_dispo: {row[0]:,} boîtes, {row[1]:,} disponibles")

            # 🆕 Vérification pièces détachées
            result = conn.execute(text("""
                SELECT categorie, COUNT(*) AS nb, SUM(stock) AS total_stock
                FROM tbl_pieces_detachees
                GROUP BY categorie
                ORDER BY nb DESC
            """))
            rows_pd = result.fetchall()
            if rows_pd:
                print(f"\n  📦 Pièces détachées par catégorie:")
                for r in rows_pd:
                    print(f"     • {r[0]}: {r[1]:,} refs, stock total: {r[2]:,}")

            result = conn.execute(text("SELECT COUNT(*) FROM tbl_pieces_mouvements"))
            row = result.fetchone()
            print(f"  📦 tbl_pieces_mouvements: {row[0]:,} mouvements")

    except Exception as e:
        print(f"  ⚠️  Erreur vérification: {e}")

    print("\n🎉 Tout est prêt !")


if __name__ == "__main__":
    main()