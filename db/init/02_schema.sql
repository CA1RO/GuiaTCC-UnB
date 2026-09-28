-- ============================================================
-- GuiaOrientador-UnB — Schema Principal
-- Baseado na Aba 3 (Modelos) da planilha de projeto.
-- ============================================================

-- ── Departamento ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS departamento (
    id_departamento  SERIAL PRIMARY KEY,
    nome             VARCHAR(200) NOT NULL UNIQUE,
    sigla            VARCHAR(20),
    faculdade        VARCHAR(200),
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_departamento_nome ON departamento USING btree (nome);

-- ── Docente ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS docente (
    id_docente       SERIAL PRIMARY KEY,
    nome             VARCHAR(300) NOT NULL,
    email            VARCHAR(200),
    titulacao        VARCHAR(100),
    link_lattes      VARCHAR(500),
    id_lattes        VARCHAR(50) UNIQUE,
    id_departamento  INTEGER REFERENCES departamento(id_departamento),
    situacao         VARCHAR(50) DEFAULT 'ativo',
    data_atualizacao TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_docente_nome         ON docente USING btree (nome);
CREATE INDEX idx_docente_departamento ON docente USING btree (id_departamento);
CREATE INDEX idx_docente_id_lattes    ON docente USING btree (id_lattes);
CREATE INDEX idx_docente_nome_trgm    ON docente USING gin (nome gin_trgm_ops);

-- ── Projeto de Pesquisa ────────────────────────────────────
CREATE TABLE IF NOT EXISTS projeto_pesquisa (
    id_projeto       SERIAL PRIMARY KEY,
    id_docente       INTEGER NOT NULL REFERENCES docente(id_docente) ON DELETE CASCADE,
    titulo           VARCHAR(500) NOT NULL,
    descricao        TEXT,
    ano_inicio       INTEGER,
    ano_fim          INTEGER,
    status           VARCHAR(50) DEFAULT 'ativo',
    palavras_chave   TEXT[],
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_projeto_docente ON projeto_pesquisa USING btree (id_docente);
CREATE INDEX idx_projeto_status  ON projeto_pesquisa USING btree (status);
CREATE INDEX idx_projeto_anos    ON projeto_pesquisa USING btree (ano_inicio, ano_fim);

-- ── Chunk Vetorial (embeddings semânticos) ─────────────────
-- Modelo vetorial — desnormalizado conforme ADR.
CREATE TABLE IF NOT EXISTS chunk_vetorial (
    id_chunk         SERIAL PRIMARY KEY,
    id_docente       INTEGER NOT NULL REFERENCES docente(id_docente) ON DELETE CASCADE,
    id_projeto       INTEGER REFERENCES projeto_pesquisa(id_projeto) ON DELETE SET NULL,
    conteudo_texto   TEXT NOT NULL,
    embedding_vetor  vector(1536),
    metadados_json   JSONB DEFAULT '{}',
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chunk_docente        ON chunk_vetorial USING btree (id_docente);
CREATE INDEX idx_chunk_projeto        ON chunk_vetorial USING btree (id_projeto);
CREATE INDEX idx_chunk_metadados      ON chunk_vetorial USING gin (metadados_json);

-- Índice HNSW para busca vetorial aproximada (ANN)
-- m=16, ef_construction=200: bom equilíbrio recall vs. velocidade
CREATE INDEX idx_chunk_embedding_hnsw ON chunk_vetorial
    USING hnsw (embedding_vetor vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);

-- ── Estudante ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS estudante (
    id_estudante     SERIAL PRIMARY KEY,
    matricula        VARCHAR(20) UNIQUE,
    nome             VARCHAR(300) NOT NULL,
    curso            VARCHAR(200),
    areas_interesse  TEXT[],
    tema_pretendido  TEXT,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_estudante_matricula ON estudante USING btree (matricula);

-- ── Sessão de Interação (Chat RAG) ─────────────────────────
-- Modelo documento — desnormalizado com JSONB para histórico.
CREATE TABLE IF NOT EXISTS sessao_interacao (
    id_sessao          SERIAL PRIMARY KEY,
    id_estudante       INTEGER REFERENCES estudante(id_estudante) ON DELETE SET NULL,
    prompt_pergunta    TEXT NOT NULL,
    resposta_rag       TEXT,
    docentes_sugeridos JSONB DEFAULT '[]',
    feedback_nota      SMALLINT CHECK (feedback_nota BETWEEN 1 AND 5),
    data_hora          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    metadados          JSONB DEFAULT '{}'
);

CREATE INDEX idx_sessao_estudante ON sessao_interacao USING btree (id_estudante);
CREATE INDEX idx_sessao_data      ON sessao_interacao USING btree (data_hora);

-- ── Função auxiliar para updated_at automático ─────────────
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers de updated_at
CREATE TRIGGER set_updated_at_departamento
    BEFORE UPDATE ON departamento FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_docente
    BEFORE UPDATE ON docente FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_projeto_pesquisa
    BEFORE UPDATE ON projeto_pesquisa FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_estudante
    BEFORE UPDATE ON estudante FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
