# Entrega 1 - Fonte OLTP modelada e populada

A primeira entrega estabelece a base de dados inicial do GuiaOrientador-UnB. O objetivo é demonstrar que uma fonte pública brasileira pode ser modelada, migrada e carregada automaticamente de maneira reproduzível.

## Conteúdo da entrega

| Requisito | Onde está documentado |
| --- | --- |
| Domínio brasileiro e pergunta de gestão | **Domínio e pergunta** |
| Esquema físico versionado | **Esquema e migrações** |
| Carga automática e idempotente | **Carga reproduzível** |
| Volume superior a uma amostra mínima | **Volume** |
| Leituras, escritas, acesso e latência | **Caracterização da carga** |
| Estratégia de atualização e histórico | **Histórico da origem** |
| Decisão de modelagem medida | **ADR 0001** |

## Resultado

A fonte selecionada foi o conjunto de docentes da pós-graduação publicado pela CAPES, filtrado para a Universidade de Brasília.

| Conjunto | Registros |
| --- | ---: |
| Docentes distintos | 2.016 |
| Programas de pós-graduação | 102 |
| Vínculos docente–programa–ano | 2.472 |

Use o menu desta aba para consultar cada requisito e sua evidência.
