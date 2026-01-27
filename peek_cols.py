import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path("db/dms.sqlite")

with sqlite3.connect(DB_PATH) as c:
    df = pd.read_sql_query('SELECT * FROM "tbl_Types_moteurs" LIMIT 5', c)
    print("COLONNES tbl_Types_moteurs:")
    print(list(df.columns))
    print(df.head(2).to_string(index=False))

