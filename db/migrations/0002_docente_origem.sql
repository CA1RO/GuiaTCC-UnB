-- Delta para um banco que já rodou db/init antes desta revisão.
-- Idempotente: um volume novo, criado por 02_schema.sql, também aceita este arquivo.

ALTER TABLE docente ADD COLUMN IF NOT EXISTS data_ingresso_orgao DATE;
ALTER TABLE docente ADD COLUMN IF NOT EXISTS data_lotacao DATE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_docente_nome ON docente (nome);
