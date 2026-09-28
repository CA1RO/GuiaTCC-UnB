# Caracterização da carga de trabalho

Números medidos no PostgreSQL 16 do Compose, com a fonte pública já carregada. A reprodução está em `scripts/medir_modelagem_origem.py`.

## Volume

- 2.797 docentes e 86 unidades no arquivo público.
- 2.607 ativos permanentes.
- Tabela `docente` com 2.802 linhas e 2.792 kB, incluindo os cinco docentes de exemplo e os índices.
- O recurso público foi criado em 01/09/2021, alterado em 13/04/2023, e o metadado do conjunto foi alterado em 01/08/2023. Em pouco mais de dois anos o portal publicou um recorte, não um fluxo diário.

## Taxa de escrita

A origem institucional é um recorte completo. Cada publicação substitui a foto anterior. Uma carga semanal, se o arquivo mudasse toda semana, reescreveria cerca de 2.797 linhas. O histórico publicado não mostra essa frequência: há um recurso, com a última alteração em abril de 2023.

A escrita contínua do sistema é outra: perfil de estudante e sessão de chat, uma linha por ação do aluno. Isso não é a origem dos docentes.

## Taxa de leitura e padrão de acesso

A leitura que a pergunta de gestão faz é agregação por unidade com filtro de situação, e busca pontual por nome.

Medição em 28/09/2026, cache quente (`shared hit`), uma execução:

| Consulta | Plano | Tempo de execução |
| --- | --- | ---: |
| Ativos permanentes por sigla da unidade | varredura de `docente` (195 linhas fora do filtro), hash join com `departamento`, agregação | 0,971 ms |
| Docente pelo nome exato `ABIMAEL DE JESUS BARROS COSTA` | índice único | 0,018 ms |

O padrão é filtro por situação, junção pela chave da unidade e busca por nome. Não é varredura analítica de janela histórica.

## Latência tolerada

A busca que o aluno espera na interface cabe em 100 ms, limite já assumido para a consulta principal. As duas consultas medidas ficam abaixo de 1 ms nesse volume.

## Sazonalidade

O cadastro docente muda no ritmo de posse, redistribuição e contrato. O uso do sistema concentra o pico quando a graduação define TCC e quando abrem PIBIC e PIBITI. A origem não acompanha esse pico: o arquivo permanece o mesmo entre publicações do portal.
