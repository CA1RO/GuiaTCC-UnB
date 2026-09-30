# Caracterização da carga de trabalho

| Aspecto            | Caracterização da E1                                                                                           |
| ------------------ | -------------------------------------------------------------------------------------------------------------- |
| Volume inicial     | 2.016 docentes, 102 programas e 2.472 vínculos anuais                                                          |
| Escrita            | Lote anual da CAPES; cerca de 4.590 upserts na carga de 2024                                                   |
| Leitura            | Busca por docente, programa e área; listagem de programas; agregações por área                                 |
| Proporção esperada | 95% de leituras e 5% de escritas durante o uso da aplicação                                                    |
| Padrão de acesso   | Leituras interativas; escrita em lote durante a inicialização ou atualização anual                             |
| Latência tolerada  | p95 de até 300 ms para consultas filtradas; até 5 minutos para a carga completa no ambiente de desenvolvimento |

## Escrita

A CAPES publica o conjunto em edições anuais. A escrita acontece em lote, não a cada consulta do estudante. Na carga de 2024 são processados 2.016 docentes, 102 programas e 2.472 vínculos.

## Leitura

O uso esperado é predominantemente de leitura. As consultas procuram docentes por nome, programa ou área, listam os programas associados a um docente e produzem contagens por área ou programa.

## Hipóteses a validar

A proporção entre leituras e escritas e as metas de latência são hipóteses iniciais de projeto. Elas devem ser verificadas com telemetria quando a aplicação tiver uso real. Os volumes, por outro lado, foram medidos diretamente na edição de 2024.
