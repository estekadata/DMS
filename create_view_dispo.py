import sqlite3
from pathlib import Path

DB_PATH = Path("db/dms.sqlite")

SQL = r"""
DROP VIEW IF EXISTS v_moteurs_dispo;

CREATE VIEW v_moteurs_dispo AS
WITH last_exped AS (
  SELECT
    em.N_moteur,
    MAX(em.DateValidation) AS derniere_date_expedition
  FROM tbl_EXPEDITIONS_moteurs em
  GROUP BY em.N_moteur
),
last_exped_price AS (
  -- récupère le prix de vente associé à la dernière date (au cas où)
  SELECT
    em.N_moteur,
    em.PrixVenteMoteur AS dernier_prix_vente,
    em.DateValidation AS derniere_date_expedition
  FROM tbl_EXPEDITIONS_moteurs em
  JOIN last_exped le
    ON le.N_moteur = em.N_moteur
   AND le.derniere_date_expedition = em.DateValidation
)
SELECT
  e.*,
  CASE WHEN lep.N_moteur IS NULL THEN 1 ELSE 0 END AS est_disponible,
  lep.derniere_date_expedition,
  lep.dernier_prix_vente
FROM v_moteurs_enrichis e
LEFT JOIN last_exped_price lep
  ON lep.N_moteur = e.N_moteur;
"""

def main():
    with sqlite3.connect(DB_PATH) as c:
        c.executescript(SQL)
    print("✅ Vue créée: v_moteurs_dispo")

if __name__ == "__main__":
    main()

