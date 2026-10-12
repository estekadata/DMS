#!/usr/bin/env python3
"""
Reimport pieces détachées : vide tbl_pieces_detachees + tbl_pieces_mouvements
puis ré-importe les 5 fichiers Excel de stock (CLIM, CALC, CREM, DÉMARREURS,
ALTERNATEURS) avec les vraies valeurs de stock.

Usage:
    cd /home/valentin/DMS
    poetry run python Script/reimport_pieces.py
    poetry run python Script/reimport_pieces.py /chemin/vers/dossier/excel

Par défaut, lit dans ~/Downloads/ (où l'utilisateur dépose les fichiers
récents). Variable d'env DATABASE_URL pour pointer vers Supabase
(sinon fallback sur la valeur dans sync_access.py).
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# Réutilise les parsers existants — ils sont déjà testés et corrects.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from Transfert_supabase import (
    _parse_compressors,
    _parse_steering,
    _parse_starters,
    _parse_calculators,
    _find_stock_col,
    _safe_int,
)

DEFAULT_DATABASE_URL = (
    "postgresql://postgres.ybaqkghlphxvkjmvtcly:1QoAroELqbzQDh9v"
    "@aws-1-eu-west-1.pooler.supabase.com:6543/postgres"
)
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def _parse_alternators(excel_dir: Path) -> tuple[list[dict], list[dict]]:
    """Parse Stock ALTERNATEURS.xls → stock + mouvements (par feuille annuelle).

    Le fichier a une feuille par année (Stock 2026, Stock 2025…). On ne prend
    que la dernière année dispo (la plus récente) pour le stock courant — les
    autres années ne représentent pas le stock actuel.

    Structure de chaque feuille :
      row 0 : "LISTE DES ALTERNATEURS" (titre)
      row 1 : entêtes (col 1 = "Références", col last = "Stock")
      row 2 : sous-entête éventuel
      row 3+ : données (col 1 = ref, col last = stock courant, cols intermédiaires = sorties)
    """
    path = excel_dir / "Stock ALTERNATEURS.xls"
    stock_rows: list[dict] = []
    mvt_rows: list[dict] = []
    if not path.exists():
        # tente la version sans espace ou variantes
        for cand in excel_dir.glob("Stock ALTERNATEURS*.xls*"):
            path = cand
            break
    if not path.exists():
        print(f"  ⚠️  Fichier non trouvé: {path}")
        return stock_rows, mvt_rows

    try:
        xls = pd.ExcelFile(path, engine="xlrd")
    except Exception as e:
        print(f"  ❌ Erreur ouverture alternateurs: {e}")
        return stock_rows, mvt_rows

    # Trouve la feuille Stock la plus récente
    stock_sheets = sorted(
        [s for s in xls.sheet_names if s.lower().startswith("stock ")],
        reverse=True,
    )
    if not stock_sheets:
        print("  ⚠️  Aucune feuille 'Stock <année>' trouvée dans alternateurs")
        return stock_rows, mvt_rows
    sheet = stock_sheets[0]
    print(f"  📄 Alternateurs : feuille {sheet} retenue (la plus récente)")

    raw = pd.read_excel(xls, sheet_name=sheet, header=None)
    stock_col = _find_stock_col(raw)
    if stock_col is None:
        print(f"  ⚠️  Pas de colonne stock détectée dans {sheet}")
        return stock_rows, mvt_rows

    # Détecte la ligne dates (souvent row 0 ou 1)
    dates_row = pd.Series()
    for r in range(min(3, len(raw))):
        row = raw.iloc[r]
        date_count = sum(1 for v in row if isinstance(v, pd.Timestamp))
        if date_count >= 5:
            dates_row = row.iloc[2:stock_col]
            break

    seen_refs: set[str] = set()
    for i in range(3, len(raw)):
        ref = str(raw.iloc[i, 1]).strip() if pd.notna(raw.iloc[i, 1]) else ""
        if not ref or ref.upper() in ("NAN", ""):
            continue
        if ref in seen_refs:
            continue
        seen_refs.add(ref)
        qty = _safe_int(raw.iloc[i, stock_col])
        stock_rows.append({
            "categorie": "Alternateur",
            "marque": "",
            "reference": ref,
            "modele": "",
            "ref_constructeur": "",
            "observations": "",
            "stock": qty,
        })
        # Mouvements (sorties datées)
        for j in range(2, stock_col):
            val = _safe_int(raw.iloc[i, j])
            if val == 0:
                continue
            dt = dates_row.iloc[j - 2] if (j - 2) < len(dates_row) else None
            dt_parsed = pd.to_datetime(dt, errors="coerce")
            if pd.notna(dt_parsed):
                mvt_rows.append({
                    "categorie": "Alternateur",
                    "reference": ref,
                    "date_mouvement": dt_parsed,
                    "quantite": val,
                    "client": "",
                })

    print(f"  ✅ Alternateurs: {len(stock_rows)} refs, {len(mvt_rows)} mouvements")
    return stock_rows, mvt_rows


def main() -> int:
    if len(sys.argv) > 1:
        excel_dir = Path(sys.argv[1]).expanduser().resolve()
    else:
        excel_dir = Path.home() / "Downloads"
    excel_dir = excel_dir.resolve()

    if not excel_dir.is_dir():
        print(f"❌ Dossier introuvable : {excel_dir}")
        return 1

    print(f"📁 Lecture des fichiers Excel dans : {excel_dir}")
    print(f"🔌 Connexion à : {DATABASE_URL.split('@')[1]}")

    all_stock: list[dict] = []
    all_mvts: list[dict] = []

    for parser in (
        _parse_compressors,
        _parse_steering,
        _parse_starters,
        _parse_calculators,
        _parse_alternators,
    ):
        s, m = parser(excel_dir)
        all_stock.extend(s)
        all_mvts.extend(m)

    if not all_stock:
        print("❌ Aucune donnée extraite. Vérifie que les fichiers Excel sont dans le bon dossier.")
        print("   Fichiers attendus :")
        print("    - Stock COMPRESSEURS CLIM.xlsx")
        print("    - Stock CALC-BSI-BSM-ABS-COM.xlsx")
        print("    - Stock CREM-PDA-COLONNES.xlsx")
        print("    - Stock DEMARREURS.xls")
        print("    - Stock ALTERNATEURS.xls")
        return 1

    # Stats
    df_stock = pd.DataFrame(all_stock)
    df_stock["stock"] = pd.to_numeric(df_stock["stock"], errors="coerce").fillna(0).astype(int)
    by_cat = df_stock.groupby("categorie").agg(
        refs=("reference", "count"),
        avec_stock=("stock", lambda s: int((s > 0).sum())),
        total_unites=("stock", "sum"),
    )
    print("\n📊 Récapitulatif extraction :")
    print(by_cat.to_string())
    print(f"\n  → {len(df_stock):,} références extraites au total ({int(df_stock['stock'].sum()):,} unités)")
    if all_mvts:
        print(f"  → {len(all_mvts):,} mouvements historiques extraits")

    # Confirmation
    answer = input("\n⚠️  Cette opération va VIDER tbl_pieces_detachees et tbl_pieces_mouvements puis tout réinsérer. Confirmer ? [o/N] ")
    if answer.strip().lower() not in ("o", "oui", "y", "yes"):
        print("Abandonné.")
        return 0

    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    except Exception as e:
        print(f"❌ Connexion DB échouée : {e}")
        return 1

    # Truncate + insert stock
    print("\n💾 Mise à jour de la base...")
    # Ajoute les colonnes manquantes (cas où la table a été créée sans elles)
    with engine.connect() as conn:
        for stmt in [
            "ALTER TABLE tbl_pieces_detachees ADD COLUMN IF NOT EXISTS ref_constructeur TEXT DEFAULT ''",
            "ALTER TABLE tbl_pieces_detachees ADD COLUMN IF NOT EXISTS observations TEXT DEFAULT ''",
            "ALTER TABLE tbl_pieces_detachees ADD COLUMN IF NOT EXISTS modele TEXT DEFAULT ''",
            "ALTER TABLE tbl_pieces_detachees ADD COLUMN IF NOT EXISTS marque TEXT DEFAULT ''",
        ]:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                print(f"  ⚠️  {stmt} → {str(e)[:120]}")
        conn.commit()
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE tbl_pieces_detachees RESTART IDENTITY CASCADE"))
        conn.commit()
    df_stock.to_sql("tbl_pieces_detachees", engine, if_exists="append", index=False, method="multi", chunksize=500)
    print(f"  ✅ tbl_pieces_detachees : {len(df_stock):,} références insérées")

    # Truncate + insert mouvements
    if all_mvts:
        df_mvts = pd.DataFrame(all_mvts)
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE tbl_pieces_mouvements RESTART IDENTITY CASCADE"))
            conn.commit()
        for i in range(0, len(df_mvts), 5000):
            chunk = df_mvts.iloc[i:i + 5000]
            chunk.to_sql("tbl_pieces_mouvements", engine, if_exists="append", index=False, method="multi", chunksize=500)
        print(f"  ✅ tbl_pieces_mouvements : {len(df_mvts):,} mouvements insérés")

    print("\n🎉 Terminé. Recharge la page /pieces sur le site pour voir les bons stocks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
