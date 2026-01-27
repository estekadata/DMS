#!/usr/bin/env python3
"""
Migration Excel → Supabase PostgreSQL
Multirex DMS

Usage:
    python migrate_to_supabase.py

Prérequis:
    pip install pandas openpyxl psycopg2-binary sqlalchemy
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
    
    # Schéma
    schema_path = Path(__file__).parent / "supabase_schema.sql"
    if schema_path.exists():
        run_schema(engine, schema_path)
    else:
        print(f"  ⚠️  Schéma non trouvé: {schema_path}")
        print("     Assurez-vous d'avoir exécuté le schéma manuellement dans Supabase")
    
    # Import des données
    print("\n📦 Import des données...")
    total_imported = 0
    
    for excel_file, table_name, column_mapping in IMPORT_ORDER:
        excel_path = EXCEL_DIR / excel_file
        count = import_excel_to_postgres(engine, excel_path, table_name, column_mapping)
        total_imported += count
    
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
            
            # Test v_boites_dispo
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) AS total,
                    SUM(CASE WHEN est_disponible = 1 THEN 1 ELSE 0 END) AS dispo
                FROM v_boites_dispo
            """))
            row = result.fetchone()
            print(f"  📦 v_boites_dispo: {row[0]:,} boîtes, {row[1]:,} disponibles")
            
    except Exception as e:
        print(f"  ⚠️  Erreur vérification: {e}")
    
    print("\n🎉 Tout est prêt !")


if __name__ == "__main__":
    main()
