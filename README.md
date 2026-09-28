# GuiaOrientador-UnB

Sistema para ajudar alunos da Universidade de Brasília a encontrar temas e orientadores de TCC e monografia. A dor que ele trata é a assimetria de informação no campus: o estudante muitas vezes não sabe quais docentes pesquisam a área dele, inclusive em outros departamentos, nem se esses docentes têm projetos ativos. O resultado costuma ser uma escolha tardia ou desorientada.

Quem usa são alunos de graduação da UnB, em especial quem está definindo o tema do TCC ou pleiteando bolsa PIBIC/PIBITI.

Disciplina: Sistema de Banco de Dados 2, turma 03, 2026.2.

## Equipe

| Nome                              | Papel no pipeline de dados |
| --------------------------------- | -------------------------- |
| Lucas Macedo Barboza              | Integrante                 |
| Caetano Santos Lucio              | Integrante                 |
| Cairo Florenço                    | Integrante                 |
| Leonardo Sobrinho                 | Integrante                 |
| Carlos Eduardo Mendes de Mesquita | Integrante                 |
| Bruna                             | Integrante                 |
| Lais                              | Integrante                 |

## O que o sistema faz

O aluno descreve um tema em linguagem natural, por exemplo “processamento de linguagem natural” ou “visão computacional”. O GuiaOrientador cruza essa pergunta com o cadastro de docentes, os projetos de pesquisa e os trechos dos currículos, e devolve orientadores próximos daquele assunto.

Na interface em `http://localhost:8000` dá para:

- buscar docente por nome ou departamento;
- abrir o perfil, com titulação, e-mail e projetos;
- perguntar o tema na conversa;
- salvar o perfil do estudante (curso, áreas de interesse e tema pretendido) para associar as próximas perguntas a ele.

## De onde vêm os dados

| Fonte                | Quem gera                                    | O que contém                                                                          | Chegada                       |
| -------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------- |
| Dados abertos da UnB | Portal de Dados Abertos / DPO / DEG          | Nome, departamento, titulação, e-mail institucional e situação funcional dos docentes | CSV ou API CKAN, em lote      |
| Currículos Lattes    | Plataforma Lattes, preenchida pelos docentes | Resumo, áreas CNPq, artigos, projetos e orientações                                   | XML, em lote                  |
| Perfil do estudante  | O próprio aluno, no sistema                  | Matrícula, curso, áreas de interesse e tema de TCC                                    | Formulário web, em tempo real |
| Consultas do chat    | O aluno na interface                         | Texto da dúvida e histórico da conversa                                               | HTTP JSON, em tempo real      |

Docentes e currículos são dado pessoal. A planilha registra a base legal de cada fonte (obrigação legal e políticas públicas para os dados abertos; dado manifestamente público para o Lattes; consentimento para o perfil do estudante).

## Como o dado é guardado

A decisão registrada pela equipe é usar **PostgreSQL 16 com a extensão pgvector** como banco único, relacional e vetorial. O volume previsto é da ordem de 20 mil vetores, com busca semântica abaixo de 100 ms e garantia ACID no cadastro. A equipe já trabalha com SQL, e o orçamento fica em ferramentas de código aberto.

Duas alternativas foram consideradas e deixadas de lado:

- um banco vetorial dedicado (Pinecone ou Milvus) ao lado de um PostgreSQL separado, porque o volume não justifica operar e sincronizar dois SGBDs;
- MongoDB com Vector Search, porque o núcleo do domínio (docente, departamento, projeto) exige integridade referencial que um modelo só de documento enfraqueceria.

| Conjunto                                  | Onde fica                                            | Por quê                                                                          |
| ----------------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------- |
| Docentes, departamentos e projetos        | Tabelas relacionais no PostgreSQL, com índice B-tree | Integridade referencial e consulta por chave em poucos milissegundos             |
| Currículos brutos e Parquet intermediário | Object storage S3, camadas bronze e silver           | Reprocessar o lote sem depender do banco da aplicação                            |
| Trechos de texto e metadados              | PostgreSQL, texto e JSONB                            | Metadados heterogêneos sem migração de schema a cada publicação                  |
| Embeddings (1536 dimensões)               | pgvector, índice HNSW                                | Busca aproximada dos vizinhos mais próximos, no lugar de varrer todos os vetores |
| Sessão do chat                            | PostgreSQL, JSONB                                    | Histórico de mensagens e docentes sugeridos                                      |
| Cache de prompts e sessões                | Redis                                                | Evitar chamar o modelo de embedding de novo para a mesma pergunta                |

O desenho original da planilha previa MinIO como data lake. As imagens públicas do MinIO deixaram de poder ser baixadas sem login. O projeto sobe o **SeaweedFS** no lugar, falando o mesmo protocolo S3. O cliente da aplicação não muda.

## Modelo

| Entidade            | Representa                                    | Modelo                   |
| ------------------- | --------------------------------------------- | ------------------------ |
| Docente             | Professor disponível para orientação          | Relacional, normalizado  |
| Projeto de pesquisa | Linha temática ou produção do docente         | Relacional, normalizado  |
| Chunk vetorial      | Trecho de resumo ou publicação, com embedding | Vetorial, desnormalizado |
| Sessão de interação | Pergunta do aluno, resposta e feedback        | Documento (JSONB)        |
| Estudante           | Perfil de quem está buscando orientador       | Relacional               |

As perguntas que o sistema precisa responder:

1. Quais orientadores de um departamento pesquisam um tema descrito em linguagem natural? Busca vetorial com filtro relacional, cerca de 1.500 vezes por dia, na tela de busca e no chat.
2. Quais projetos ativos um docente coordena? Junção por chave, cerca de 800 vezes por dia, na página do perfil.
3. Quantas recomendações foram feitas por departamento no semestre, e qual a nota média de feedback? Agregação SQL, cerca de 30 vezes por dia, no relatório da coordenação.

## Pipeline

O dado acadêmico muda devagar, então a carga é semanal e em lote. Só a conversa com o aluno é contínua.

1. **Ingestão (domingo, 02h).** Baixa dados abertos da UnB e XML do Lattes e grava a camada bronze, imutável.
2. **Limpeza (domingo, 04h).** Extrai o XML, normaliza nomes, tira HTML e deduplica artigos entre coautores. Sai Parquet na camada silver e as tabelas relacionais.
3. **Embeddings (domingo, 06h).** Corta o texto em janelas de 512 tokens com sobreposição de 64, gera vetores de 1536 dimensões e grava `chunk_vetorial`.
4. **Conversa, sob demanda.** Gera o embedding da pergunta, busca os 5 trechos mais próximos, monta o contexto e registra a sessão. O cache fica no Redis.

Se a chave da OpenAI não estiver configurada, a interface e o cadastro funcionam, mas a busca semântica ainda não gera os vetores nem a resposta do modelo.

## Como rodar

Requisitos: Docker e Docker Compose.

```bash
cp .env.example .env
docker compose up -d
```

Abra http://localhost:8000.

| Serviço             | Endereço                   |
| ------------------- | -------------------------- |
| Interface e API     | http://localhost:8000      |
| Documentação da API | http://localhost:8000/docs |
| PostgreSQL          | localhost:5432             |
| Redis               | localhost:6379             |
| S3 (SeaweedFS)      | http://localhost:8333      |

Para carregar departamentos, docentes e projetos de exemplo:

```bash
docker compose exec api python -m scripts.seed_dados_exemplo
```

Esse comando vale uma vez. Nomes de departamento e IDs Lattes são únicos, então uma segunda execução falha.

Para ativar embeddings e a resposta do chat, preencha `OPENAI_API_KEY` no `.env` e suba de novo:

```bash
docker compose up -d
```

## Riscos que a equipe assumiu

- A extração do Lattes pode cair por limite de taxa ou mudança de layout. A mitigação é guardar o bruto imutável e só promover um lote que passe na validação.
- XML heterogêneo gera docente duplicado. A chave estável é o ID Lattes; o que não fecha vai para uma fila de rejeição.
- O índice HNSW pode estourar a memória se a base crescer sem particionar. A decisão deve ser reaberta se passar de 500 mil vetores ou se a latência P99 da busca passar de 200 ms.
- Cota ou indisponibilidade do provedor de embeddings derruba o chat. O Redis guarda perguntas repetidas, e a busca relacional cobre o caso em que o modelo externo não responde.
