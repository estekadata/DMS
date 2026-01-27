-- ============================================
-- SCHEMA SUPABASE pour Multirex DMS
-- Généré à partir des fichiers Excel
-- ============================================

-- Supprimer les tables existantes (dans l'ordre des dépendances)
DROP VIEW IF EXISTS v_moteurs_dispo CASCADE;
DROP VIEW IF EXISTS v_boites_dispo CASCADE;

DROP TABLE IF EXISTS breaker_free_offers CASCADE;
DROP TABLE IF EXISTS breaker_click_offers CASCADE;
DROP TABLE IF EXISTS breakers CASCADE;

DROP TABLE IF EXISTS tbl_pieces CASCADE;
DROP TABLE IF EXISTS tbl_expeditions_moteurs CASCADE;
DROP TABLE IF EXISTS tbl_expeditions_boites CASCADE;
DROP TABLE IF EXISTS tbl_factures CASCADE;
DROP TABLE IF EXISTS tbl_expeditions CASCADE;
DROP TABLE IF EXISTS tbl_moteurs CASCADE;
DROP TABLE IF EXISTS tbl_boites CASCADE;
DROP TABLE IF EXISTS tbl_receptions CASCADE;
DROP TABLE IF EXISTS tbl_clients CASCADE;
DROP TABLE IF EXISTS tbl_fournisseurs CASCADE;
DROP TABLE IF EXISTS tbl_emplacements CASCADE;
DROP TABLE IF EXISTS tbl_affectations CASCADE;
DROP TABLE IF EXISTS tbl_energie CASCADE;
DROP TABLE IF EXISTS tbl_etats_divers CASCADE;
DROP TABLE IF EXISTS tbl_marques CASCADE;
DROP TABLE IF EXISTS tbl_pays CASCADE;

-- ============================================
-- TABLES DE RÉFÉRENCE (lookup tables)
-- ============================================

CREATE TABLE tbl_affectations (
    n_affectation INTEGER PRIMARY KEY,
    nom_affectation TEXT,
    selection_affectation BOOLEAN DEFAULT FALSE
);

CREATE TABLE tbl_emplacements (
    id_emplacement INTEGER PRIMARY KEY,
    nom_emplacement TEXT,
    selection_emplacement BOOLEAN DEFAULT FALSE
);

CREATE TABLE tbl_energie (
    n_energie INTEGER PRIMARY KEY,
    nom_energie TEXT,
    nom_energie_anglais TEXT
);

CREATE TABLE tbl_etats_divers (
    n_etat INTEGER PRIMARY KEY,
    etat TEXT,
    etat_anglais TEXT,
    selection_etat BOOLEAN DEFAULT FALSE,
    abreviation TEXT
);

CREATE TABLE tbl_marques (
    n_marque INTEGER PRIMARY KEY,
    nom_marque TEXT,
    selection_marque BOOLEAN DEFAULT FALSE
);

CREATE TABLE tbl_pays (
    n_pays INTEGER PRIMARY KEY,
    nom_pays TEXT,
    selection_pays BOOLEAN DEFAULT FALSE
);

-- ============================================
-- TABLES PRINCIPALES
-- ============================================

CREATE TABLE tbl_fournisseurs (
    n_fournisseur INTEGER PRIMARY KEY,
    nom_fournisseur TEXT,
    contact_fourniss TEXT,
    adresse1_fourniss TEXT,
    adresse2_fourniss TEXT,
    cp_fourniss TEXT,
    ville_fourniss TEXT,
    tel_fourniss TEXT,
    fax_fourniss TEXT,
    port_fourniss TEXT,
    mail_fourniss TEXT,
    autres_infos TEXT,
    actionnaire BOOLEAN DEFAULT FALSE,
    careco BOOLEAN DEFAULT FALSE,
    n_attribue TEXT,
    afficher BOOLEAN DEFAULT TRUE
);

CREATE TABLE tbl_clients (
    n_client INTEGER PRIMARY KEY,
    societe TEXT,
    titre_contact TEXT,
    nom_contact TEXT,
    prenom_contact TEXT,
    nom_usage TEXT,
    adresse TEXT,
    ville TEXT,
    code_postal TEXT,
    pays INTEGER REFERENCES tbl_pays(n_pays),
    tel TEXT,
    fax TEXT,
    email TEXT,
    remarques TEXT,
    e_r TEXT,
    afficher_deroulant BOOLEAN DEFAULT TRUE,
    ident_tva TEXT,
    n_regroup_clt INTEGER
);

CREATE TABLE tbl_receptions (
    n_reception INTEGER PRIMARY KEY,
    n_fournisseur INTEGER REFERENCES tbl_fournisseurs(n_fournisseur),
    date_achat TIMESTAMP,
    montant_ht NUMERIC(12,2),
    facture BOOLEAN DEFAULT FALSE,
    date_facture_fourniss TIMESTAMP,
    reception_terminee BOOLEAN DEFAULT FALSE,
    dossier_classe BOOLEAN DEFAULT FALSE,
    liste_grillages TEXT,
    autres_info TEXT
);

CREATE TABLE tbl_expeditions (
    n_expedition INTEGER PRIMARY KEY,
    n_client INTEGER REFERENCES tbl_clients(n_client),
    date_chargement TIMESTAMP,
    type_container TEXT,
    ref_container TEXT,
    n_plomb TEXT,
    nb_cartons INTEGER,
    nb_palettes INTEGER,
    poids INTEGER,
    tare_container INTEGER,
    n_transitaire TEXT,
    montant_ht NUMERIC(12,2),
    autres_info TEXT,
    num_facture TEXT,
    expedition_terminee BOOLEAN DEFAULT FALSE,
    cloture_dossier BOOLEAN DEFAULT FALSE,
    moteurs_completes BOOLEAN DEFAULT FALSE,
    frais_manut NUMERIC(12,2),
    cfr NUMERIC(12,2),
    petites_pieces NUMERIC(12,2)
);

CREATE TABLE tbl_moteurs (
    n_moteur INTEGER PRIMARY KEY,
    num_interne_moteur TEXT,
    num_reception INTEGER REFERENCES tbl_receptions(n_reception),
    n_type_moteur INTEGER,
    num_serie TEXT,
    modele_saisi TEXT,
    compo_moteur INTEGER,
    info_bv TEXT,
    type_bv TEXT,
    num_interne_bv TEXT,
    n_affectation INTEGER REFERENCES tbl_affectations(n_affectation),
    ref_pi TEXT,
    type_pi TEXT,
    etat_moteur INTEGER,
    etat_carter INTEGER,
    observations TEXT,
    prix_achat_moteur NUMERIC(12,2),
    date_resa_moteur TIMESTAMP,
    resa_client_moteur TEXT,
    utilisateur TEXT,
    date_modif TIMESTAMP,
    pointage_inventaire BOOLEAN DEFAULT FALSE,
    pointage2 BOOLEAN DEFAULT FALSE,
    alternateur INTEGER DEFAULT 0,
    demarreur INTEGER DEFAULT 0,
    carburateur INTEGER DEFAULT 0,
    allumeur INTEGER DEFAULT 0,
    pav INTEGER DEFAULT 0,
    pompe_inj INTEGER DEFAULT 0,
    turbo INTEGER DEFAULT 0,
    injecteurs INTEGER DEFAULT 0,
    compresseur INTEGER DEFAULT 0,
    pda INTEGER DEFAULT 0,
    embrayage INTEGER DEFAULT 0,
    autre TEXT,
    geloc_mot TEXT,
    compo_init TEXT,
    poids_moteur INTEGER,
    date_modif2 TIMESTAMP,
    utilisateur_modif TEXT,
    selection_moteur_tble BOOLEAN DEFAULT FALSE,
    code_moteur TEXT,
    date_sortie TIMESTAMP,
    archiver BOOLEAN DEFAULT FALSE,
    n_expedition INTEGER
);

CREATE INDEX idx_moteurs_code ON tbl_moteurs(code_moteur);
CREATE INDEX idx_moteurs_reception ON tbl_moteurs(num_reception);
CREATE INDEX idx_moteurs_expedition ON tbl_moteurs(n_expedition);

CREATE TABLE tbl_boites (
    n_bv INTEGER PRIMARY KEY,
    num_interne_bv TEXT,
    n_reception INTEGER REFERENCES tbl_receptions(n_reception),
    type_bv INTEGER,
    ref_bv TEXT,
    num_interne_moteur TEXT,
    achat_bv NUMERIC(12,2),
    date_resa_bv TIMESTAMP,
    resa_client_bv TEXT,
    observations_bv TEXT,
    utilisateur TEXT,
    date_modif TIMESTAMP,
    id_emplacement INTEGER REFERENCES tbl_emplacements(id_emplacement),
    prix_vte_bv NUMERIC(12,2),
    date_vente_bv TIMESTAMP,
    stock BOOLEAN DEFAULT TRUE,
    vendu BOOLEAN DEFAULT FALSE,
    pointage_inventaire BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_boites_reception ON tbl_boites(n_reception);

CREATE TABLE tbl_expeditions_moteurs (
    id SERIAL PRIMARY KEY,
    n_expedition INTEGER REFERENCES tbl_expeditions(n_expedition),
    n_moteur INTEGER REFERENCES tbl_moteurs(n_moteur),
    prix_vente_moteur NUMERIC(12,2),
    date_validation TIMESTAMP
);

CREATE INDEX idx_exp_moteurs_date ON tbl_expeditions_moteurs(date_validation);
CREATE INDEX idx_exp_moteurs_moteur ON tbl_expeditions_moteurs(n_moteur);

CREATE TABLE tbl_expeditions_boites (
    id SERIAL PRIMARY KEY,
    n_expedition INTEGER REFERENCES tbl_expeditions(n_expedition),
    n_bv INTEGER REFERENCES tbl_boites(n_bv),
    prix_vente_bv NUMERIC(12,2),
    date_validation TIMESTAMP
);

CREATE INDEX idx_exp_boites_date ON tbl_expeditions_boites(date_validation);

CREATE TABLE tbl_factures (
    num_piece TEXT PRIMARY KEY,
    n_client INTEGER REFERENCES tbl_clients(n_client),
    n_expedition INTEGER,
    type_de_piece TEXT,
    date_facture TIMESTAMP,
    annee_fact INTEGER,
    ref_container TEXT,
    export NUMERIC(12,2),
    exp_cee NUMERIC(12,2),
    exp_tva NUMERIC(12,2),
    r_tva NUMERIC(12,2),
    r_cee NUMERIC(12,2),
    susp_tva NUMERIC(12,2),
    autre_prest NUMERIC(12,2),
    port_tva NUMERIC(12,2),
    port_exo NUMERIC(12,2),
    ex_a_num1 BOOLEAN DEFAULT FALSE,
    ex_a BOOLEAN DEFAULT FALSE,
    connaissements BOOLEAN DEFAULT FALSE,
    deb BOOLEAN DEFAULT FALSE,
    facture_acquittee BOOLEAN DEFAULT FALSE,
    reste_a_solder NUMERIC(12,2),
    transitaire TEXT,
    transitaire_hors_liste TEXT,
    observations_facture TEXT,
    dossier_classe BOOLEAN DEFAULT FALSE,
    relance_transit TEXT
);

CREATE TABLE tbl_pieces (
    id SERIAL PRIMARY KEY,
    n_reception INTEGER REFERENCES tbl_receptions(n_reception),
    qte INTEGER,
    n_type_piece INTEGER,
    modele_piece TEXT,
    pu_piece NUMERIC(12,2),
    total_ha_piece NUMERIC(12,2)
);

-- ============================================
-- TABLES CASSES (breakers)
-- ============================================

CREATE TABLE breakers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE breaker_click_offers (
    id SERIAL PRIMARY KEY,
    breaker_id INTEGER NOT NULL REFERENCES breakers(id),
    code_moteur TEXT NOT NULL,
    marque TEXT,
    energie TEXT,
    type_nom TEXT,
    type_modele TEXT,
    type_annee TEXT,
    prix_demande NUMERIC(12,2),
    qty INTEGER DEFAULT 1,
    note TEXT,
    immatriculation TEXT,
    vin TEXT,
    photo_moteur_path TEXT,
    photo_plaque_path TEXT,
    audio_path TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE breaker_free_offers (
    id SERIAL PRIMARY KEY,
    breaker_id INTEGER NOT NULL REFERENCES breakers(id),
    texte TEXT NOT NULL,
    prix_demande NUMERIC(12,2),
    note TEXT,
    immatriculation TEXT,
    vin TEXT,
    photo_moteur_path TEXT,
    photo_plaque_path TEXT,
    audio_path TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- VUES
-- ============================================

CREATE VIEW v_moteurs_dispo AS
SELECT 
    m.*,
    ma.nom_marque AS marque,
    e.nom_energie AS energie,
    -- Type moteur info (à ajuster selon vos données)
    m.n_type_moteur::TEXT AS type_nom,
    m.modele_saisi AS type_modele,
    EXTRACT(YEAR FROM r.date_achat)::TEXT AS type_annee,
    CASE 
        WHEN m.archiver = TRUE THEN 0
        WHEN m.n_expedition IS NOT NULL THEN 0
        WHEN EXISTS (
            SELECT 1 FROM tbl_expeditions_moteurs em 
            WHERE em.n_moteur = m.n_moteur
        ) THEN 0
        ELSE 1
    END AS est_disponible
FROM tbl_moteurs m
LEFT JOIN tbl_receptions r ON r.n_reception = m.num_reception
LEFT JOIN tbl_fournisseurs f ON f.n_fournisseur = r.n_fournisseur
LEFT JOIN tbl_marques ma ON ma.n_marque = m.n_type_moteur  -- À ajuster selon mapping réel
LEFT JOIN tbl_energie e ON e.n_energie = m.compo_moteur;   -- À ajuster selon mapping réel

CREATE VIEW v_boites_dispo AS
SELECT 
    b.*,
    CASE 
        WHEN b.stock = TRUE AND (b.vendu IS NULL OR b.vendu = FALSE) THEN 1
        ELSE 0
    END AS est_disponible
FROM tbl_boites b;

-- ============================================
-- PERMISSIONS (RLS désactivé pour simplifier)
-- ============================================
-- Si vous voulez activer RLS plus tard:
-- ALTER TABLE tbl_moteurs ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Allow all" ON tbl_moteurs FOR ALL USING (true);

COMMENT ON VIEW v_moteurs_dispo IS 'Vue des moteurs avec statut de disponibilité';
COMMENT ON VIEW v_boites_dispo IS 'Vue des boîtes avec statut de disponibilité';
