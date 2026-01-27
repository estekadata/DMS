import sqlite3
from pathlib import Path

DB_PATH = Path("db/dms.sqlite")

SQL = r"""
DROP VIEW IF EXISTS v_moteurs_enrichis;

CREATE VIEW v_moteurs_enrichis AS
SELECT
  -- Moteur (stock)
  m.N_moteur,
  m.NumInterneMoteur,
  m.NumRéception,
  m.NumSérie,
  m.N_TypeMoteur,
  m.CodeMoteur,
  m.[ModèleSaisi],
  m.CompoMoteur,
  m.EtatMoteur,
  m.EtatCarter,
  m.Archiver,
  m.DateSortie,
  m.Observations,
  m.PrixAchatMoteur,
  m.DateRésaMoteur,
  m.[RésaClientMoteur],

  -- Type moteur (référentiel)
  tm.N_marque AS type_N_marque,
  tm.[Nom TypeMoteur] AS type_nom,
  tm.[Modèle TypeMoteur] AS type_modele,
  tm.N_Energie AS type_N_energie,
  tm.ObsEnergie AS type_obs_energie,
  tm.Année AS type_annee,
  tm.[Particularité TypeMoteur] AS type_particularite,
  tm.EquivalenceTypeMoteur AS type_equivalence,
  tm.PrixVenteMBV AS type_prix_vente_mbv,
  tm.PrixVenteMSeul AS type_prix_vente_seul,
  tm.HSCode AS type_hscode,
  tm.PrixAchatBaseTypeMot AS type_prix_achat_base,

  -- Marque
  mar.[NOM Marque] AS marque,

  -- Energie
  en.[Nom Energie] AS energie

FROM tbl_MOTEURS m
LEFT JOIN tbl_Types_moteurs tm
  ON tm.N_TypeMoteur = m.N_TypeMoteur
LEFT JOIN tbl_Marques mar
  ON mar.N_marque = tm.N_marque
LEFT JOIN tbl_Energie en
  ON en.N_Energie = tm.N_Energie
;
"""

def main():
    with sqlite3.connect(DB_PATH) as c:
        c.executescript(SQL)
    print("✅ Vue créée: v_moteurs_enrichis")

if __name__ == "__main__":
    main()

