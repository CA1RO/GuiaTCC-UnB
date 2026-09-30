# Carga reproduzível

Um único comando cria o ambiente, aplica a migração, baixa a fonte pública e popula o banco:

```bash
cp .env.example .env
docker compose up --build
```

O fluxo executado pelo Compose é:

1. iniciar o PostgreSQL 16 com pgvector;
2. executar as migrações Alembic em ordem;
3. baixar o CSV oficial da CAPES;
4. ler o arquivo em fluxo e filtrar `SG_ENTIDADE_ENSINO = UNB`;
5. consolidar docentes, programas e vínculos;
6. fazer upsert das três estruturas;
7. iniciar a API depois da conclusão da carga.

Não há CSV copiado para o repositório, preenchimento manual ou dependência de uma chave da OpenAI para realizar a carga da E1.

## Verificação

```bash
docker compose exec postgres psql \
  -U guia_orientador \
  -d guia_orientador_db \
  -c "SELECT (SELECT count(*) FROM docente) AS docentes, (SELECT count(*) FROM programa_pos_graduacao) AS programas, (SELECT count(*) FROM docente_programa) AS vinculos;"
```

Resultado esperado para a edição de 2024:

```text
 docentes | programas | vinculos
----------+-----------+----------
     2016 |       102 |     2472
```

## Idempotência

Para executar novamente o carregador:

```bash
docker compose run --rm loader
```

Docentes usam `id_capes`, programas usam `codigo_capes` e vínculos usam a chave composta `(id_docente, id_programa, ano_base)`. Por isso, repetir a mesma carga atualiza os registros existentes sem aumentar as contagens.
