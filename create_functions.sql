-- 1. get_ventes_mois_count
CREATE OR REPLACE FUNCTION get_ventes_mois_count()
RETURNS JSON AS $$
SELECT json_build_object(
  'n', COUNT(*)::int,
  'ca', COALESCE(SUM(prix_vente_moteur), 0)::float
)
FROM tbl_expeditions_moteurs
WHERE date_validation >= date_trunc('month', NOW())
  AND prix_vente_moteur IS NOT NULL;
$$ LANGUAGE sql;

-- 2. get_ventes_mois_prec_count
CREATE OR REPLACE FUNCTION get_ventes_mois_prec_count()
RETURNS JSON AS $$
SELECT json_build_object(
  'n', COUNT(*)::int,
  'ca', COALESCE(SUM(prix_vente_moteur), 0)::float
)
FROM tbl_expeditions_moteurs
WHERE date_validation >= date_trunc('month', NOW()) - INTERVAL '1 month'
  AND date_validation < date_trunc('month', NOW())
  AND prix_vente_moteur IS NOT NULL;
$$ LANGUAGE sql;

-- 3. get_receptions_mois_count
CREATE OR REPLACE FUNCTION get_receptions_mois_count()
RETURNS JSON AS $$
SELECT json_build_object(
  'n', (SELECT COUNT(*)::int FROM tbl_receptions WHERE date_achat >= date_trunc('month', NOW())),
  'nb_mot', (SELECT COUNT(*)::int FROM tbl_moteurs m JOIN tbl_receptions r ON r.n_reception = m.num_reception WHERE r.date_achat >= date_trunc('month', NOW()))
);
$$ LANGUAGE sql;

-- 4. get_marge_mois
CREATE OR REPLACE FUNCTION get_marge_mois()
RETURNS JSON AS $$
SELECT json_build_object(
  'marge', COALESCE(SUM(em.prix_vente_moteur) - SUM(m.prix_achat_moteur), 0)::float,
  'pct', CASE WHEN SUM(em.prix_vente_moteur) > 0
    THEN ROUND(((SUM(em.prix_vente_moteur) - SUM(m.prix_achat_moteur)) / SUM(em.prix_vente_moteur) * 100)::numeric, 1)::float
    ELSE 0 END
)
FROM tbl_expeditions_moteurs em
JOIN tbl_moteurs m ON m.n_moteur = em.n_moteur
WHERE em.date_validation >= date_trunc('month', NOW())
  AND em.prix_vente_moteur IS NOT NULL AND em.prix_vente_moteur > 0
  AND m.prix_achat_moteur IS NOT NULL AND m.prix_achat_moteur > 0;
$$ LANGUAGE sql;

-- 5. get_prix_moyens_mois
CREATE OR REPLACE FUNCTION get_prix_moyens_mois()
RETURNS JSON AS $$
SELECT json_build_object(
  'prix_vente_moy', COALESCE((SELECT AVG(prix_vente_moteur)::float FROM tbl_expeditions_moteurs WHERE date_validation >= date_trunc('month', NOW()) AND prix_vente_moteur > 0), 0),
  'prix_achat_moy', COALESCE((SELECT AVG(m.prix_achat_moteur)::float FROM tbl_moteurs m JOIN tbl_receptions r ON r.n_reception = m.num_reception WHERE r.date_achat >= date_trunc('month', NOW()) AND m.prix_achat_moteur > 0), 0)
);
$$ LANGUAGE sql;

-- 6. get_besoins_moteurs
-- Groupe par nom_type_moteur (ex: K9K 764, F9Q 674) depuis tbl_types_moteurs
CREATE OR REPLACE FUNCTION get_besoins_moteurs(p_limit int DEFAULT 100)
RETURNS TABLE(
  code_moteur text,
  type_moteur text,
  marque text,
  energie text,
  nb_vendus_3m bigint,
  nb_stock_dispo bigint,
  prix_moy_achat_3m numeric
) AS $$
WITH ventes AS (
    SELECT tm.nom_type_moteur, COUNT(*) AS nb_vendus_3m
    FROM tbl_expeditions_moteurs em
    JOIN tbl_moteurs m ON m.n_moteur = em.n_moteur
    JOIN tbl_types_moteurs tm ON tm.n_type_moteur = m.n_type_moteur
    WHERE em.date_validation >= NOW() - INTERVAL '3 months'
      AND tm.nom_type_moteur IS NOT NULL AND TRIM(tm.nom_type_moteur) <> ''
    GROUP BY tm.nom_type_moteur
),
achats AS (
    SELECT tm.nom_type_moteur,
           AVG(CASE WHEN r.date_achat >= NOW() - INTERVAL '3 months' THEN m.prix_achat_moteur END) AS prix_moy_3m
    FROM tbl_moteurs m
    JOIN tbl_receptions r ON r.n_reception = m.num_reception
    JOIN tbl_types_moteurs tm ON tm.n_type_moteur = m.n_type_moteur
    WHERE m.prix_achat_moteur IS NOT NULL AND r.date_achat IS NOT NULL
    GROUP BY tm.nom_type_moteur
),
stock AS (
    SELECT tm.nom_type_moteur,
           MAX(ma.nom_marque) AS marque,
           MAX(en.nom_energie) AS energie,
           COUNT(*) AS nb_stock_dispo
    FROM tbl_moteurs m
    JOIN tbl_types_moteurs tm ON tm.n_type_moteur = m.n_type_moteur
    LEFT JOIN tbl_marques ma ON ma.n_marque = tm.n_marque
    LEFT JOIN tbl_energie en ON en.n_energie = COALESCE(tm.n_energie, m.compo_moteur)
    WHERE m.n_expedition IS NULL
      AND (m.archiver IS NULL OR m.archiver = false)
      AND (m.resa_client_moteur IS NULL OR TRIM(m.resa_client_moteur) = '')
    GROUP BY tm.nom_type_moteur
)
SELECT v.nom_type_moteur AS code_moteur,
       LEFT(v.nom_type_moteur, 3) AS type_moteur,
       COALESCE(s.marque, '') AS marque,
       COALESCE(s.energie, '') AS energie,
       v.nb_vendus_3m,
       COALESCE(s.nb_stock_dispo, 0) AS nb_stock_dispo,
       ROUND(a.prix_moy_3m, 2) AS prix_moy_achat_3m
FROM ventes v
LEFT JOIN achats a ON a.nom_type_moteur = v.nom_type_moteur
LEFT JOIN stock s ON s.nom_type_moteur = v.nom_type_moteur
ORDER BY v.nb_vendus_3m DESC
LIMIT p_limit;
$$ LANGUAGE sql;

-- 7. search_moteurs
CREATE OR REPLACE FUNCTION search_moteurs(
  p_search text DEFAULT '',
  p_statut text DEFAULT '',
  p_limit int DEFAULT 500
)
RETURNS TABLE(
  n_moteur int,
  code_moteur text,
  num_serie text,
  modele_saisi text,
  prix_achat_moteur numeric,
  marque text,
  energie text,
  statut text,
  resa_client_moteur text,
  fournisseur text,
  date_achat timestamp
) AS $$
SELECT m.n_moteur, COALESCE(tm.nom_type_moteur, m.code_moteur) AS code_moteur,
       m.num_serie, m.modele_saisi, m.prix_achat_moteur,
       ma.nom_marque AS marque, e.nom_energie AS energie,
       CASE WHEN m.n_expedition IS NOT NULL OR m.archiver = true THEN 'Vendu/Archivé'
            WHEN m.resa_client_moteur IS NOT NULL AND TRIM(m.resa_client_moteur) <> '' THEN 'Réservé'
            ELSE 'Disponible' END AS statut,
       m.resa_client_moteur,
       f.nom_fournisseur AS fournisseur,
       r.date_achat
FROM tbl_moteurs m
LEFT JOIN tbl_receptions r ON r.n_reception = m.num_reception
LEFT JOIN tbl_fournisseurs f ON f.n_fournisseur = r.n_fournisseur
LEFT JOIN tbl_types_moteurs tm ON tm.n_type_moteur = m.n_type_moteur
LEFT JOIN tbl_marques ma ON ma.n_marque = tm.n_marque
LEFT JOIN tbl_energie e ON e.n_energie = COALESCE(tm.n_energie, m.compo_moteur)
WHERE (p_search = '' OR UPPER(COALESCE(tm.nom_type_moteur, m.code_moteur)) LIKE '%' || UPPER(p_search) || '%'
       OR UPPER(m.num_serie) LIKE '%' || UPPER(p_search) || '%')
  AND (p_statut = '' OR p_statut = 'Tous'
       OR (p_statut = 'Disponible' AND m.n_expedition IS NULL AND (m.archiver IS NULL OR m.archiver = false) AND (m.resa_client_moteur IS NULL OR TRIM(m.resa_client_moteur) = ''))
       OR (p_statut = 'Réservé' AND m.resa_client_moteur IS NOT NULL AND TRIM(m.resa_client_moteur) <> '' AND m.n_expedition IS NULL)
       OR (p_statut = 'Vendu/Archivé' AND (m.n_expedition IS NOT NULL OR m.archiver = true)))
ORDER BY m.n_moteur DESC
LIMIT p_limit;
$$ LANGUAGE sql;
