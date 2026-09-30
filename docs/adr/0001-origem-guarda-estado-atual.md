# 0001 — O cadastro de docentes guarda o estado atual e sobrescreve lotação e situação

- **Status:** aceito
- **Data:** 2026-09-28
- **Decisores:** Lucas Macedo Barboza, Caetano Santos Lucio, Cairo Florenço, Leonardo Sobrinho, Carlos Eduardo Mendes de Mesquita, Bruna, Lais

## Contexto

A origem é o arquivo público de docentes da UnB: 2.797 pessoas, 86 unidades, 2.607 ativos permanentes. O recurso tem uma alteração registrada em 13/04/2023. A pergunta de gestão pede o estado vigente: quem está em exercício, em que unidade e com qual situação.

A equipe opera PostgreSQL 16 no Docker Compose e escreve SQL. O dado é pessoal e já é publicado pela universidade. O salário líquido vem no arquivo e fica de fora do modelo, porque a pergunta não o usa.

Há dois tempos no mesmo registro. A data de ingresso e a data de lotação são eventos da fonte. `data_atualizacao` e `updated_at` marcam a ingestão neste banco.

A unidade fica normalizada em `departamento`. O arquivo repete 86 nomes em 2.797 linhas, sem colisão de grafia.

## Alternativas consideradas

### A. Opção nula: permanecer no seed fictício

Cinco docentes e um punhado de projetos de exemplo sobem com `scripts/seed_dados_exemplo.py` e bastam para exercitar a interface. A carga é manual no sentido de que o dado não vem da fonte pública, e o volume não responde quem está lotado na UnB. A agregação de ativos permanentes sobre esse seed devolve zero, porque a situação de exemplo é `ativo`, não `ATIVO PERMANENTE`.

### B. Insert-only: acrescentar um recorte inteiro a cada carga

Cada execução guardaria outra cópia das 2.797 linhas, com `carregado_em`. A pergunta de estado atual passaria a filtrar `carregado_em = max(carregado_em)`. Um ano de carga semanal, se o arquivo mudasse, chegaria a cerca de 145 mil linhas (52 × 2.797) e ainda assim a pergunta útil continuaria sendo a do último recorte. O ganho real só aparece se a gestão passar a comparar duas datas. O arquivo publicado hoje não traz essas datas: baixar o mesmo 7z duas vezes duplica a mesma foto.

### C. CRUD de estado atual, com unidade normalizada

Um registro por pessoa, upsert pelo nome, unidade em `departamento` com chave estrangeira. A carga substitui titulação, situação, unidade e as duas datas de evento. A pergunta de gestão é um filtro e uma junção, sem escolher o recorte mais novo.

## Medição

Dado: a carga pública no PostgreSQL 16 do Compose, em 28/09/2026. Comando:

```bash
docker compose exec api python -m scripts.carregar_dados_abertos
docker compose exec api python -m scripts.medir_modelagem_origem
```

O script de medição monta dois recortes da fonte (5.594 linhas) e compara com a tabela atual. Plano com cache quente.

| Alternativa                   | Linhas usadas na pergunta |        Agregação de ativos por unidade |                         Busca por nome |
| ----------------------------- | ------------------------: | -------------------------------------: | -------------------------------------: |
| A. Seed fictício              |                         5 | não produz os 2.607 ativos permanentes |                          fora da fonte |
| B. Insert-only, dois recortes |                     5.594 |                               1,725 ms | exige o recorte de `max(carregado_em)` |
| C. Estado atual               |                     2.802 |                               0,971 ms |             0,018 ms pelo índice único |

A tabela `docente` ocupava 2.792 kB com índices. A cópia temporária dos dois recortes, sem os índices da tabela principal, ocupava 1.096 kB.

## Decisão

Escolhemos o estado atual. `docente` tem uma linha por nome, `departamento` guarda a unidade, e a carga faz upsert. `data_ingresso_orgao` e `data_lotacao` copiam o evento da fonte. `data_atualizacao` e `updated_at` marcam a ingestão.

## Consequências

**O que ganhamos:** a contagem de ativos permanentes por unidade sai em 0,971 ms, e o nome resolve em 0,018 ms. A chave estrangeira impede docente sem unidade cadastrada. A segunda carga mantém 2.802 linhas.

**O que perdemos:** a lotação e a situação anteriores saem da tabela no upsert. Não há como responder em que unidade a pessoa estava em uma data passada a partir de `docente`. A data de lotação visível é sempre a do último arquivo aplicado.

**O que se torna irreversível:** depois do upsert, o valor relacional anterior só volta se o objeto bruto daquela execução ainda estiver no bucket `bronze` e for reprocessado. O bronze de dois downloads do arquivo de 2023 não recupera a lotação de 2021. Voltar para insert-only a partir daqui exige guardar os recortes futuros; o passado que o upsert já substituiu não reaparece.

## Gatilho de revisão

Reabrir esta decisão se a pergunta de gestão passar a exigir a lotação numa data anterior, ou se a agregação de ativos permanentes por unidade passar de 100 ms.
