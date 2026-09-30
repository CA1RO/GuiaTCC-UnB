# Esquema físico e migrações

O esquema da origem vive em SQL versionado e roda em ordem a partir de um banco vazio.

1. `db/init/01_extensions.sql` cria `vector`, `pg_trgm` e `unaccent`.
2. `db/init/02_schema.sql` cria as tabelas, chaves, checagens, índices e os gatilhos de `updated_at`.
3. `db/migrations/0002_docente_origem.sql` acrescenta `data_ingresso_orgao`, `data_lotacao` e o índice único de `docente.nome`. A revisão Alembic `0002_docente_origem` executa esse mesmo arquivo. O comando de carga também o executa, então um volume que já existia antes desta revisão fica alinhado sem passo manual.

No Docker Compose, o PostgreSQL monta `db/init` em `docker-entrypoint-initdb.d`. Um volume novo aplica os dois primeiros arquivos na ordem dos nomes. Esses scripts não rodam de novo em um volume que já tem dados.

Integridade que o banco impõe:

- `departamento.nome` é único e obrigatório.
- `docente.nome` é único. É a chave natural do arquivo público, que tem 2.797 nomes distintos em 2.797 linhas.
- `docente.id_departamento` referencia `departamento`.
- `projeto_pesquisa.id_docente` referencia `docente` e o tipo só aceita `pesquisa`, `extensao` ou `tcc`.
- `sessao_interacao.feedback_nota` só aceita 1 a 5.
- `chunk_vetorial.embedding_vetor` é `vector(1536)`.

`departamento` fica em tabela própria. As 2.797 pessoas se distribuem em 86 unidades, e o nome da unidade não se repete com grafias diferentes no arquivo. Guardar a unidade só como texto dentro de `docente` repetiria o mesmo nome e deixaria a agregação por sigla sem chave.

O salário líquido vem no arquivo e não entra no banco. A pergunta de gestão não usa remuneração.

Para um terceiro conferir do zero:

```bash
docker compose down -v
docker compose up -d --build
docker compose exec api python -m scripts.carregar_dados_abertos
```

`down -v` apaga o volume. Use só quando a intenção for recriar o banco.
