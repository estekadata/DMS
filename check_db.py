import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path("db/dms.sqlite")

def q(sql):
    with sqlite3.connect(DB_PATH) as c:
        return pd.read_sql_query(sql, c)

print(q("SELECT COUNT(*) as n FROM tbl_MOTEURS"))
print(q("SELECT COUNT(*) as n FROM tbl_Types_moteurs"))
print(q("SELECT COUNT(*) as n FROM tbl_Marques"))
print(q("SELECT COUNT(*) as n FROM tbl_EXPEDITIONS_moteurs"))
