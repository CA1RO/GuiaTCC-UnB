# Carga reprodutível

Um comando baixa a fonte pública e popula `departamento` e `docente`. Não há CSV versionado no repositório e não há etapa manual.

```bash
docker compose up -d --build
docker compose exec api python -m scripts.carregar_dados_abertos
```

O script `scripts/carregar_dados_abertos.py`:

1. baixa `dados_institucionais_docentes.7z` de [dados.unb.br](https://dados.unb.br/pt_PT/dataset/docentes);
2. grava o arquivo bruto, com data e hora no caminho, no bucket `bronze`;
3. abre o 7z, lê o CSV em Latin-1 com separador `;`;
4. faz upsert das 86 unidades e dos 2.797 docentes.

A segunda execução não duplica linha. Depois de duas cargas seguidas, o banco ficou com 2.802 docentes: 2.797 da fonte e 5 do exemplo local, que têm nome diferente e por isso sobrevivem ao upsert. Unidades: 91, pelas mesmas cinco do exemplo.

O upsert atualiza titulação, situação, unidade, `data_ingresso_orgao` e `data_lotacao`. Preserva `linha_pesquisa`, e-mail e ID Lattes, porque o arquivo público não traz esses campos.

O pacote `py7zr` está em `requirements.txt`. A imagem da API precisa ser construída com `--build` para incluí-lo.
