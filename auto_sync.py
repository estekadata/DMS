#!/usr/bin/env python3
"""
MultirexDMS AutoSync — synchronisation Access -> Supabase SANS interface.

Pensé pour être packagé en .exe (pyinstaller) et lancé par une tâche planifiée
Windows (ouverture de session + quotidienne, avec rattrapage). Réutilise la même
logique que l'updater manuel (sync_access.process_table, mode "apply") : écrit
donc dans la table import_log Supabase, consultable sur la page Synchronisation
du site. En plus, écrit un journal LOCAL (logs/autosync.log) à côté de l'exe,
indispensable pour diagnostiquer sur le PC du client même hors ligne.

Chemin de la base Access, par ordre de priorité :
    1. 1er argument de ligne de commande               (ex: AutoSync.exe "D:\\Base\\Achats_données.accdb")
    2. variable d'environnement MULTIREX_ACCDB
    3. fichier accdb_path.txt placé à côté de l'exe     (1 ligne = le chemin)
    4. défaut : C:\\Multirex\\Achats_données.accdb

Codes de sortie : 0 = succès, 1 = au moins une table en échec, 2 = base
introuvable, 3 = driver Access manquant, 4 = tables manquantes dans le .accdb.

Packaging (sur Windows) :
    pip install pyinstaller pyodbc pandas sqlalchemy psycopg2-binary
    pyinstaller --onefile --name MultirexDMS_AutoSync auto_sync.py
"""

from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine

from sync_access import (
    DATABASE_URL,
    TABLES_CONFIG,
    check_mdbtools,
    list_access_tables,
    process_table,
)

USER_TAG = "auto@multirex"  # apparaît dans import_log.mode / user
DEFAULT_ACCDB = r"C:\Multirex\Achats_données.accdb"
MAX_LOG_LINES = 3000


def base_dir() -> Path:
    """Dossier de l'exe (mode figé pyinstaller) ou du script."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def resolve_accdb() -> Path | None:
    # 1) argument CLI
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return Path(sys.argv[1].strip().strip('"'))
    # 2) variable d'environnement
    env = os.environ.get("MULTIREX_ACCDB")
    if env and env.strip():
        return Path(env.strip().strip('"'))
    # 3) fichier de config à côté de l'exe
    cfg = base_dir() / "accdb_path.txt"
    if cfg.exists():
        for line in cfg.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                return Path(line.strip('"'))
    # 4) défaut
    d = Path(DEFAULT_ACCDB)
    return d if d.exists() else None


def log_path() -> Path:
    d = base_dir() / "logs"
    try:
        d.mkdir(exist_ok=True)
    except Exception:
        d = base_dir()
    return d / "autosync.log"


def emit(msg: str) -> None:
    """Ajoute une ligne horodatée au journal local (rotation simple)."""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line)  # visible si lancé à la main en console
    path = log_path()
    try:
        prev = path.read_text(encoding="utf-8", errors="ignore").splitlines() if path.exists() else []
        prev.append(line)
        if len(prev) > MAX_LOG_LINES:
            prev = prev[-MAX_LOG_LINES:]
        path.write_text("\n".join(prev) + "\n", encoding="utf-8")
    except Exception:
        pass


def main() -> int:
    emit("=== Démarrage AutoSync ===")

    accdb = resolve_accdb()
    if accdb is None:
        emit(
            "ERREUR: base Access introuvable. Indique son chemin dans accdb_path.txt "
            f"(à côté de l'exe) ou via MULTIREX_ACCDB. Défaut cherché: {DEFAULT_ACCDB}"
        )
        return 2
    if not accdb.exists():
        emit(f"ERREUR: fichier introuvable: {accdb}")
        return 2

    try:
        check_mdbtools()
    except Exception as e:
        emit(f"ERREUR driver Access (pyodbc) : {e}")
        return 3

    try:
        tables = list_access_tables(accdb)
        expected = [c["access_table"] for c in TABLES_CONFIG]
        missing = [t for t in expected if t not in tables]
        if missing:
            emit(f"ERREUR: tables manquantes dans le .accdb : {missing}")
            return 4

        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        tot_new = tot_upd = tot_skip = 0
        failed: list[str] = []

        for cfg in TABLES_CONFIG:
            try:
                stats = process_table(engine, accdb, cfg, "apply", USER_TAG)
                tot_new += int(stats.get("new", 0) or 0)
                tot_upd += int(stats.get("updated", 0) or 0)
                tot_skip += int(stats.get("errors", 0) or 0)
            except Exception as e:
                failed.append(f"{cfg['access_table']}: {e}")
                emit(f"  ⛔ {cfg['access_table']} -> {e}")

        summary = f"{tot_new} ajoutées, {tot_upd} modifiées, {tot_skip} ignorées"
        if failed:
            emit(f"TERMINÉ AVEC ERREURS — {summary} ; {len(failed)} table(s) en échec : {failed}")
            return 1
        emit(f"OK — {summary} (source: {accdb.name})")
        return 0

    except Exception as e:
        emit(f"ERREUR globale : {e}")
        emit(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
