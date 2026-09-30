# Esquema físico e migrações

O esquema é criado por uma migração Alembic versionada em `alembic/versions/20260930_0001_schema_inicial.py`. Ela parte de um PostgreSQL vazio, habilita as extensões necessárias e cria tabelas, chaves, restrições, índices e gatilhos.

## Modelo da origem

Um docente pode participar de vários programas, e um programa pode ter vários docentes. O ano-base pertence ao vínculo.

```text
DOCENTE 1 --- N DOCENTE_PROGRAMA N --- 1 PROGRAMA_POS_GRADUACAO

docente
  PK id_docente
  UK id_capes

programa_pos_graduacao
  PK id_programa
  UK codigo_capes

docente_programa
  PK, FK id_docente
  PK, FK id_programa
  PK     ano_base
         categoria_docente
```

## Integridade

- `docente.id_capes` é único.
- `programa_pos_graduacao.codigo_capes` é único e obrigatório.
- A chave composta de `docente_programa` impede a repetição do mesmo vínculo no mesmo ano.
- As chaves estrangeiras do vínculo usam exclusão em cascata.
- `ano_fim` de um projeto não pode ser anterior a `ano_inicio`.
- A nota de feedback aceita somente valores de 1 a 5.

## Ordem automática

O serviço `migrate` espera o PostgreSQL ficar saudável e executa `alembic upgrade head`. O serviço `loader` só começa depois da migração terminar com sucesso, e a API só inicia depois da carga.

O diretório `db/init` permanece como referência legada, mas não é montado pelo Docker Compose e não participa da criação do banco.
