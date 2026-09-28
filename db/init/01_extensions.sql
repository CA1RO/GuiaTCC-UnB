-- ============================================================
-- GuiaOrientador-UnB — Extensões do PostgreSQL
-- Executado automaticamente na inicialização do container.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS vector;      -- pgvector: busca vetorial
CREATE EXTENSION IF NOT EXISTS pg_trgm;     -- Trigram: busca textual fuzzy
CREATE EXTENSION IF NOT EXISTS unaccent;    -- Remoção de acentos em buscas
