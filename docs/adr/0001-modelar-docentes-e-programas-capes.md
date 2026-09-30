# ADR 0001 — Modelar docentes e programas da CAPES com vínculo anual N:N

- **Status:** Aceito
- **Data:** 2026-09-30
- **Decisores:** equipe GuiaOrientador-UnB

## Contexto

A primeira entrega precisa carregar, de forma automática e reproduzível, uma fonte pública brasileira com volume suficiente para apoiar a pergunta de gestão:

> Quais docentes de pós-graduação da UnB atuam em programas e áreas relacionados ao tema de interesse do estudante?

A fonte escolhida é o conjunto **Docentes da Pós-Graduação Stricto Sensu do Brasil — 2024**, publicado no Portal de Dados Abertos da CAPES. O arquivo contém uma linha por vínculo entre docente, programa e ano. Depois do filtro `SG_ENTIDADE_ENSINO = UNB`, há 2.016 docentes, 102 programas e 2.472 vínculos anuais.

### 1. Caracterização da carga de trabalho

- Carga anual em lote, executada automaticamente ao iniciar o ambiente.
- Aproximadamente 2.472 gravações de vínculos por carga, além dos *upserts* de 2.016 docentes e 102 programas.
- Operação predominantemente de leitura: estimativa inicial de 95% de leituras e 5% de escritas durante o uso da aplicação.
- Acessos principais: procurar docentes por nome, programa e área; listar os programas de um docente; contar docentes por programa ou área.
- Metas iniciais: consultas filtradas com p95 de até 300 ms e carga completa em até 5 minutos, no ambiente de desenvolvimento da equipe.

### 2. Restrições não funcionais

- PostgreSQL 16 e execução local por Docker Compose.
- Migrações versionadas e banco reconstruível a partir do zero.
- Carga idempotente: executar novamente não pode duplicar docentes, programas ou vínculos.
- Nenhuma dependência de chave de API, CAPTCHA ou procedimento manual para obter os dados da E1.
- Não persistir CPF, sexo, raça, nacionalidade, data de nascimento ou faixa etária presentes no arquivo de origem, pois não são necessários para a pergunta de gestão.

## Alternativas consideradas

### A — Manter o modelo anterior sem representar programa (opção nula)

Manter apenas `departamento`, `docente` e `projeto_pesquisa`. É a opção de menor alteração, mas não representa a unidade central da fonte CAPES nem a relação de um docente com vários programas.

### B — Guardar uma tabela desnormalizada por linha do CSV

Copiar em cada vínculo os dados do docente e do programa. Simplifica a ingestão inicial, porém repete nomes, titulação, programa e área e aumenta o risco de versões divergentes do mesmo cadastro.

### C — Normalizar docente, programa e vínculo anual N:N

Criar `docente`, `programa_pos_graduacao` e `docente_programa`. O vínculo usa a chave composta `(id_docente, id_programa, ano_base)`, preservando a participação do mesmo docente em vários programas e em anos diferentes.

## 3 e 4. Protótipo e medição

A medição usa o arquivo público de 2024, filtrado para a UnB. Ela pode ser repetida com:

```bash
python -m scripts.medir_modelagem_capes
```

| Medida | Resultado |
| --- | ---: |
| Docentes distintos | 2.016 |
| Programas distintos | 102 |
| Vínculos docente–programa–ano | 2.472 |
| Docentes ligados a mais de um programa | 409 |
| Maior número de programas por docente | 5 |
| Vínculos perdidos em um modelo com um único programa por docente | 456 |
| Projeção desnormalizada | 456.148 bytes |
| Projeção normalizada | 333.912 bytes |
| Redução na projeção medida | 26,8% |

Os bytes são uma aproximação reproduzível em JSON compacto dos campos usados pelo sistema, não uma estimativa do armazenamento físico do PostgreSQL.

## Decisão

Adotar a alternativa C. Docentes e programas são entidades independentes, ligadas por `docente_programa`, com o ano-base fazendo parte da identidade do vínculo.

Quanto ao histórico, será usada uma estratégia híbrida:

- `docente` e `programa_pos_graduacao` seguem **CRUD com sobrescrita** por suas chaves públicas estáveis (`id_capes` e `codigo_capes`);
- `docente_programa` preserva o histórico anual: uma nova edição da fonte acrescenta vínculos de outro `ano_base`, enquanto uma reexecução do mesmo ano apenas atualiza a categoria do vínculo.

## 5. Consequências

### Ganhos

- Todos os 2.472 vínculos observados são preservados.
- A carga pode ser repetida sem criar duplicatas.
- Há menos repetição dos atributos de docente e programa.
- Consultas por programa, área e ano ficam expressas diretamente no modelo relacional.

### Perdas e custos

- Consultas completas exigem junções entre três tabelas.
- O carregador precisa resolver as chaves internas antes de gravar os vínculos.
- Correções retroativas publicadas pela CAPES para um mesmo ano substituem a categoria anterior, em vez de manter cada versão recebida.

### Irreversibilidade

A decisão é reversível por uma nova migração. Entretanto, reduzir o vínculo para um único programa por docente seria uma transformação com perda dos 456 vínculos adicionais já observados.

## 6. Gatilhos de revisão

Revisar esta decisão quando ocorrer pelo menos uma destas condições:

- a CAPES deixar de publicar identificadores estáveis de pessoa ou programa;
- o volume ultrapassar 1 milhão de vínculos anuais;
- a latência p95 das consultas principais ultrapassar 300 ms em três medições consecutivas, mesmo após criação ou ajuste de índices;
- a pergunta de gestão passar a exigir histórico de cada correção dentro do mesmo ano, e não apenas o retrato anual;
- o sistema incorporar outras instituições ou fontes cujas identidades não possam ser conciliadas com `id_capes` e `codigo_capes`.
