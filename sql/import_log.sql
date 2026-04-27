-- ============================================
-- IMPORT LOG / SYNC METADATA
-- À exécuter une seule fois dans Supabase SQL editor
-- ============================================

-- 1. Table de logs d'import (1 ligne par batch / table importée)
CREATE TABLE IF NOT EXISTS import_log (
    id              SERIAL PRIMARY KEY,
    started_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMP,
    source_file     TEXT,            -- nom du fichier .accdb uploadé
    table_name      TEXT NOT NULL,   -- nom de la table Supabase ciblée
    sync_strategy   TEXT NOT NULL,   -- 'incremental_datemodif' | 'incremental_date_metier' | 'full_reload'
    rows_read       INTEGER DEFAULT 0,
    rows_inserted   INTEGER DEFAULT 0,
    rows_updated    INTEGER DEFAULT 0,
    rows_skipped    INTEGER DEFAULT 0,
    error_message   TEXT,
    user_email      TEXT,            -- qui a lancé l'import
    mode            TEXT NOT NULL    -- 'preview' | 'apply'
);

CREATE INDEX IF NOT EXISTS idx_import_log_started ON import_log(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_import_log_table   ON import_log(table_name);
CREATE INDEX IF NOT EXISTS idx_import_log_mode    ON import_log(mode);

COMMENT ON TABLE import_log IS 'Trace de tous les imports Access -> Supabase (preview + apply)';

-- 2. Table de métadonnées de sync (1 ligne par table, dernière sync réussie)
CREATE TABLE IF NOT EXISTS sync_metadata (
    table_name      TEXT PRIMARY KEY,
    last_sync_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    last_max_date   TIMESTAMP,       -- max(datemodif) au moment de la sync
    last_user       TEXT
);

COMMENT ON TABLE sync_metadata IS 'Dernière date de sync par table — sert de point de départ pour le prochain import incrémental';
