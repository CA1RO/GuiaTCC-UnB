# GuiaOrientador-UnB

<<<<<<< HEAD
O **GuiaOrientador-UnB** é uma plataforma de apoio à escolha de temas e orientadores de trabalhos acadêmicos na Universidade de Brasília. O projeto busca reduzir a distância entre estudantes e docentes, reunindo informações acadêmicas que normalmente ficam dispersas entre departamentos, programas e diferentes fontes institucionais.
=======
Sistema para o aluno da UnB achar um projeto de pesquisa, extensão ou TCC alinhado à afinidade dele. Se não houver projeto nessa linha, o guia indica docentes que pesquisam algo próximo. A dor de origem, registrada na planilha, é a assimetria de informação no campus: o estudante muitas vezes não descobre o que já existe fora do próprio departamento.

> > > > > > > 32e4f30fc9e7b190fed4bbffed0f9965559805aa

O público principal são estudantes que estão definindo um tema de TCC ou monografia, procurando orientação acadêmica ou buscando oportunidades de iniciação científica.

## Visão geral

O estudante informa um tema ou uma área de interesse. A plataforma organiza dados públicos sobre docentes e programas acadêmicos para ajudar a identificar pessoas e áreas relacionadas à busca.

O projeto combina uma aplicação web com uma pipeline de dados responsável por coletar, tratar, validar e armazenar as informações usadas nas consultas.

## Como funciona

1. Dados acadêmicos públicos são obtidos de fontes oficiais.
2. A pipeline seleciona os campos necessários, normaliza os registros e evita duplicações.
3. As informações são armazenadas em um banco relacional versionado por migrações.
4. A API disponibiliza os dados para a interface e para os módulos de busca.
5. O estudante consulta docentes e áreas relacionadas ao seu tema de interesse.

## Componentes

| Componente        | Responsabilidade                                               |
| ----------------- | -------------------------------------------------------------- |
| Frontend          | Interface de consulta e interação com o estudante              |
| FastAPI           | API e regras da aplicação                                      |
| PostgreSQL        | Cadastro relacional de docentes, programas e demais entidades  |
| pgvector          | Suporte à evolução da busca por similaridade semântica         |
| Pipeline de dados | Download, transformação, validação e carga das fontes públicas |
| Alembic           | Versionamento e execução das mudanças do banco                 |
| Docker Compose    | Inicialização reproduzível dos serviços                        |

A documentação da entrega E1, para leitura em tela: [https://ca1ro.github.io/GuiaTCC-UnB/](https://ca1ro.github.io/GuiaTCC-UnB/).

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

## Executar o projeto

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

A leitura em tela está no [GitHub Pages](https://ca1ro.github.io/GuiaTCC-UnB/).

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

- aplicação: <http://localhost:8000>;
- documentação da API: <http://localhost:8000/docs>.

Projetos de pesquisa, extensão e TCC de exemplo, com linha de pesquisa, continuam em um comando separado. O arquivo público não traz projeto. Esse comando vale uma vez: nomes de departamento e IDs Lattes são únicos, então uma segunda execução falha.

```bash
python -m venv .venv-docs
source .venv-docs/bin/activate
python -m pip install -r requirements-docs.txt
mkdocs serve
```

Abra <http://127.0.0.1:8000>. O MkDocs atualiza a página automaticamente quando um arquivo em `docs/` é salvo.

## Estrutura principal

```text
alembic/      migrações do banco
docs/         documentação publicada pelo MkDocs
frontend/     interface web
scripts/      cargas e medições reproduzíveis
src/api/      rotas e serviços da API
src/db/       modelos e acesso ao banco
src/pipeline/ ingestão e transformação dos dados
tests/        testes automatizados
```
