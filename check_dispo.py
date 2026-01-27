import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path("db/dms.sqlite")

with sqlite3.connect(DB_PATH) as c:
    print(pd.read_sql_query("SELECT est_disponible, COUNT(*) as n FROM v_moteurs_dispo GROUP BY est_disponible", c))
    print(pd.read_sql_query("""
        SELECT N_moteur, CodeMoteur, marque, energie, est_disponible, derniere_date_expedition, dernier_prix_vente
        FROM v_moteurs_dispo
        ORDER BY derniere_date_expedition DESC
        LIMIT 5
    """, c).to_string(index=False))

