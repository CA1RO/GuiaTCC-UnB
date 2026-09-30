# Domínio e pergunta de gestão

A origem da E1 é o conjunto [Docentes da Pós-Graduação Stricto Sensu do Brasil — 2024](https://dadosabertos.capes.gov.br/dataset/2021-a-2024-docentes-da-pos-graduacao-stricto-sensu-no-brasil), publicado pela CAPES sob licença Creative Commons Attribution.

A carga usa o CSV oficial de 2024 e seleciona somente as linhas cuja instituição é a Universidade de Brasília, identificada por `SG_ENTIDADE_ENSINO = UNB`.

## Pergunta de gestão

Quais docentes de pós-graduação da UnB atuam em programas e áreas relacionados ao tema de interesse do estudante?

## Recorte utilizado

O recorte possui 2.016 docentes, 102 programas de pós-graduação e 2.472 vínculos entre docente, programa e ano-base.

O arquivo nacional também apresenta CPF, sexo, raça, nacionalidade, data de nascimento e faixa etária. Esses atributos não são necessários para responder à pergunta de gestão e são descartados durante a leitura, sem serem persistidos no banco.

O Lattes não é fonte desta entrega. A busca pública possui CAPTCHA e a extração oficial em lote depende de convênio institucional, portanto ela não atenderia ao requisito de carga automática e reproduzível por qualquer avaliador.
