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
    id_capes         INTEGER UNIQUE,
    nome             VARCHAR(300) NOT NULL,
    email            VARCHAR(200),
    titulacao        VARCHAR(100),
    ano_titulacao    INTEGER,
    area_titulacao   VARCHAR(200),
    tipo_vinculo     VARCHAR(100),
    regime_trabalho  VARCHAR(100),
    link_lattes      VARCHAR(500),
    id_lattes        VARCHAR(50) UNIQUE,
    id_departamento  INTEGER REFERENCES departamento(id_departamento),
    linha_pesquisa   TEXT,
    situacao         VARCHAR(50) DEFAULT 'ativo',
    -- data_ingresso_orgao e data_lotacao são hora do evento na fonte (DPO).
    -- data_atualizacao e updated_at são hora da ingestão neste banco.
    data_ingresso_orgao DATE,
    data_lotacao     DATE,
    data_atualizacao TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_docente_nome         ON docente USING btree (nome);
CREATE INDEX idx_docente_departamento ON docente USING btree (id_departamento);
CREATE INDEX idx_docente_id_lattes    ON docente USING btree (id_lattes);
CREATE INDEX idx_docente_id_capes     ON docente USING btree (id_capes);
CREATE INDEX idx_docente_nome_trgm    ON docente USING gin (nome gin_trgm_ops);
CREATE UNIQUE INDEX IF NOT EXISTS uq_docente_nome ON docente (nome);

-- ── Programa de Pós-Graduação (fonte CAPES) ───────────────
CREATE TABLE IF NOT EXISTS programa_pos_graduacao (
    id_programa                 SERIAL PRIMARY KEY,
    codigo_capes                VARCHAR(20) NOT NULL UNIQUE,
    nome                        VARCHAR(300) NOT NULL,
    grau                        VARCHAR(80),
    modalidade                  VARCHAR(80),
    conceito                    VARCHAR(10),
    area_avaliacao              VARCHAR(200),
    grande_area_conhecimento    VARCHAR(200),
    area_conhecimento           VARCHAR(200),
    municipio                   VARCHAR(150),
    uf                          VARCHAR(2),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_programa_area ON programa_pos_graduacao USING btree (area_avaliacao);

-- Um docente pode atuar em vários programas e o vínculo é anual.
CREATE TABLE IF NOT EXISTS docente_programa (
    id_docente       INTEGER NOT NULL REFERENCES docente(id_docente) ON DELETE CASCADE,
    id_programa      INTEGER NOT NULL REFERENCES programa_pos_graduacao(id_programa) ON DELETE CASCADE,
    ano_base         INTEGER NOT NULL,
    categoria_docente VARCHAR(80),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id_docente, id_programa, ano_base)
);

CREATE INDEX idx_docente_programa_programa ON docente_programa USING btree (id_programa);
CREATE INDEX idx_docente_programa_ano      ON docente_programa USING btree (ano_base);

-- ── Projeto de Pesquisa ────────────────────────────────────
CREATE TABLE IF NOT EXISTS projeto_pesquisa (
    id_projeto       SERIAL PRIMARY KEY,
    id_docente       INTEGER NOT NULL REFERENCES docente(id_docente) ON DELETE CASCADE,
    titulo           VARCHAR(500) NOT NULL,
    descricao        TEXT,
    tipo             VARCHAR(20) NOT NULL DEFAULT 'pesquisa',
    ano_inicio       INTEGER,
    ano_fim          INTEGER,
    status           VARCHAR(50) DEFAULT 'ativo',
    palavras_chave   TEXT[],
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT projeto_pesquisa_tipo_check CHECK (tipo IN ('pesquisa', 'extensao', 'tcc'))
);

CREATE INDEX idx_projeto_docente ON projeto_pesquisa USING btree (id_docente);
CREATE INDEX idx_projeto_status  ON projeto_pesquisa USING btree (status);
CREATE INDEX idx_projeto_tipo    ON projeto_pesquisa USING btree (tipo);
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

CREATE TRIGGER set_updated_at_programa_pos_graduacao
    BEFORE UPDATE ON programa_pos_graduacao FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_docente_programa
    BEFORE UPDATE ON docente_programa FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_projeto_pesquisa
    BEFORE UPDATE ON projeto_pesquisa FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_estudante
    BEFORE UPDATE ON estudante FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
