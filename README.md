# GuiaOrientador-UnB

Sistema para o aluno da UnB achar um projeto de pesquisa, extensão ou TCC alinhado à afinidade dele. Se não houver projeto nessa linha, o guia indica docentes que pesquisam algo próximo. A dor de origem, registrada na planilha, é a assimetria de informação no campus: o estudante muitas vezes não descobre o que já existe fora do próprio departamento.

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

O aluno descreve uma afinidade, por exemplo “processamento de linguagem natural” ou “álgebra linear”. A busca olha primeiro os projetos cadastrados, com tipo pesquisa, extensão ou TCC. Só quando nenhum projeto passa do limiar de semelhança a resposta muda para docentes cuja linha de pesquisa se aproxima do tema.

Na interface em `http://localhost:8000` dá para:

- filtrar por tipo de projeto e por departamento;
- abrir o projeto, com descrição, docente responsável e contato;
- ver o docente e a linha dele quando não existe projeto;
- perguntar o tema na conversa, com a mesma regra;
- salvar o perfil do estudante (curso, áreas de interesse e tema pretendido).

## De onde vêm os dados

| Fonte                | Quem gera                                    | O que contém                                                                                  | Chegada                       |
| -------------------- | -------------------------------------------- | --------------------------------------------------------------------------------------------- | ----------------------------- |
| Dados abertos da UnB | Portal de Dados Abertos / DPO / DEG          | Nome, unidade de lotação, classe e situação funcional dos docentes. O arquivo não traz e-mail | CSV compactado em 7z, em lote |
| Currículos Lattes    | Plataforma Lattes, preenchida pelos docentes | Resumo, áreas CNPq, artigos, projetos e orientações                                           | XML, em lote                  |
| Perfil do estudante  | O próprio aluno, no sistema                  | Matrícula, curso, áreas de interesse e tema de TCC                                            | Formulário web, em tempo real |
| Consultas do chat    | O aluno na interface                         | Texto da dúvida e histórico da conversa                                                       | HTTP JSON, em tempo real      |

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

| Entidade            | Representa                                                   | Modelo                   |
| ------------------- | ------------------------------------------------------------ | ------------------------ |
| Docente             | Professor e a linha de pesquisa, usada quando não há projeto | Relacional, normalizado  |
| Projeto             | Pesquisa, extensão ou TCC de um docente                      | Relacional, normalizado  |
| Chunk vetorial      | Trecho de resumo ou publicação, com embedding                | Vetorial, desnormalizado |
| Sessão de interação | Pergunta do aluno, resposta e feedback                       | Documento (JSONB)        |
| Estudante           | Perfil de quem está buscando orientador                      | Relacional               |

As perguntas que o sistema precisa responder:

1. Quais projetos de pesquisa, extensão ou TCC se alinham à afinidade do aluno? É a consulta principal, na tela de busca e no chat.
2. Se nenhum projeto se aproximar, quais docentes seguem uma linha parecida? É a alternativa, não o primeiro resultado.
3. Quantas recomendações foram feitas por departamento no semestre, e qual a nota média de feedback? Agregação SQL, no relatório da coordenação.

## Pipeline

O dado acadêmico muda devagar, então a carga é semanal e em lote. Só a conversa com o aluno é contínua.

1. **Ingestão (domingo, 02h).** Baixa dados abertos da UnB e XML do Lattes e grava a camada bronze, imutável.
2. **Limpeza (domingo, 04h).** Extrai o XML, normaliza nomes, tira HTML e deduplica artigos entre coautores. Sai Parquet na camada silver e as tabelas relacionais.
3. **Embeddings (domingo, 06h).** Corta o texto em janelas de 512 tokens com sobreposição de 64, gera vetores de 1536 dimensões e grava `chunk_vetorial`.
4. **Conversa, sob demanda.** Gera o embedding da pergunta, busca os 5 trechos mais próximos, monta o contexto e registra a sessão. O cache fica no Redis.

Se a chave da OpenAI não estiver configurada, a interface e o cadastro funcionam, mas a busca semântica ainda não gera os vetores nem a resposta do modelo.

## Entrega E1

A origem transacional desta entrega é o cadastro público de docentes da UnB. A pergunta de gestão, o esquema, a carga, o volume, a caracterização, o tratamento de histórico e o ADR estão em:

- [Domínio e pergunta de gestão](docs/e1/01-dominio-e-pergunta.md)
- [Esquema e migrações](docs/e1/02-esquema-e-migracoes.md)
- [Carga reprodutível](docs/e1/03-carga-reprodutivel.md)
- [Volume](docs/e1/04-volume.md)
- [Caracterização da carga](docs/e1/05-caracterizacao-da-carga.md)
- [Histórico da origem](docs/e1/06-historico-da-origem.md)
- [ADR 0001 — estado atual do docente](docs/adr/0001-origem-guarda-estado-atual.md)

## Como rodar

Requisitos: Docker e Docker Compose.

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec api python -m scripts.carregar_dados_abertos
```

O segundo comando baixa o arquivo público de docentes e popula o banco. Pode rodar de novo: a carga atualiza a lotação e não duplica nome. Abra http://localhost:8000.

| Serviço             | Endereço                   |
| ------------------- | -------------------------- |
| Interface e API     | http://localhost:8000      |
| Documentação da API | http://localhost:8000/docs |
| PostgreSQL          | localhost:5432             |
| Redis               | localhost:6379             |
| S3 (SeaweedFS)      | http://localhost:8333      |

Projetos de pesquisa, extensão e TCC de exemplo, com linha de pesquisa, continuam em um comando separado. O arquivo público não traz projeto. Esse comando vale uma vez: nomes de departamento e IDs Lattes são únicos, então uma segunda execução falha.

```bash
docker compose exec api python -m scripts.seed_dados_exemplo
```

Para ativar embeddings e a resposta do chat, preencha `OPENAI_API_KEY` no `.env` e suba de novo:

```bash
docker compose up -d
```

## Riscos que a equipe assumiu

- A extração do Lattes pode cair por limite de taxa ou mudança de layout. A mitigação é guardar o bruto imutável e só promover um lote que passe na validação.
- XML heterogêneo gera docente duplicado. A chave estável é o ID Lattes; o que não fecha vai para uma fila de rejeição.
- O índice HNSW pode estourar a memória se a base crescer sem particionar. A decisão deve ser reaberta se passar de 500 mil vetores ou se a latência P99 da busca passar de 200 ms.
- Cota ou indisponibilidade do provedor de embeddings derruba o chat. O Redis guarda perguntas repetidas, e a busca relacional cobre o caso em que o modelo externo não responde.
