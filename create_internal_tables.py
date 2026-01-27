import sqlite3
from pathlib import Path

DB_PATH = Path("db/dms.sqlite")

SQL = """
CREATE TABLE IF NOT EXISTS internal_needs (
  need_id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  client_name TEXT,
  code_moteur TEXT,
  marque TEXT,
  energie TEXT,
  annee TEXT,
  modele_text TEXT,
  comment TEXT
);
"""

with sqlite3.connect(DB_PATH) as c:
    c.executescript(SQL)

print("✅ Table créée: internal_needs")

