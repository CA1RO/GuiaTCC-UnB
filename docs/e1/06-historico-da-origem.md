# Histórico da origem

A origem de docentes é CRUD que sobrescreve. Cada carga faz upsert por `docente.nome` e substitui titulação, situação funcional, unidade, data de ingresso no órgão e data de lotação. O valor anterior desses campos deixa de existir na tabela.

Isso permite perguntar quem está lotado agora, em qual unidade, com qual situação e com quais datas de ingresso e de lotação vieram no último arquivo. A contagem medida é 2.607 ativos permanentes em 84 siglas.

Isso não permite perguntar qual era a unidade de uma pessoa em uma data anterior, nem quando a situação mudou. O portal entrega um arquivo único, não um log de eventos. A data de lotação gravada é a do recorte vigente. A próxima carga, se o arquivo trouxer outra data, substitui a anterior.

Dois carimbos convivem de propósito:

- `data_ingresso_orgao` e `data_lotacao` são hora do evento, copiadas do CSV (`data_ingres_orgao`, `data_lotacao`).
- `data_atualizacao` e `updated_at` são hora da ingestão neste banco, preenchidas com `NOW()` no upsert e pelo gatilho de atualização.

Confundir os dois faria um relatório tratar a hora em que o script rodou como se fosse a data em que a pessoa mudou de unidade.

`linha_pesquisa`, e-mail e ID Lattes não são sobrescritos, porque o arquivo público não os traz. `sessao_interacao` é outra tabela: cada pergunta do aluno entra como linha nova e o histórico da conversa permanece. Essa tabela não é a origem institucional.

O bruto de cada download fica no bucket `bronze`, com data e hora no caminho. Reprocessar esse objeto reconstrói o recorte daquela execução. Dois downloads do mesmo arquivo de 2023 não reconstroem a lotação de 2021, porque a fonte não publicou esse passado.
