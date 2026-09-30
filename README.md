# GuiaOrientador-UnB

O **GuiaOrientador-UnB** é uma plataforma de apoio à escolha de temas e orientadores de trabalhos acadêmicos na Universidade de Brasília. O projeto busca reduzir a distância entre estudantes e docentes, reunindo informações acadêmicas que normalmente ficam dispersas entre departamentos, programas e diferentes fontes institucionais.

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

| Componente | Responsabilidade |
| --- | --- |
| Frontend | Interface de consulta e interação com o estudante |
| FastAPI | API e regras da aplicação |
| PostgreSQL | Cadastro relacional de docentes, programas e demais entidades |
| pgvector | Suporte à evolução da busca por similaridade semântica |
| Pipeline de dados | Download, transformação, validação e carga das fontes públicas |
| Alembic | Versionamento e execução das mudanças do banco |
| Docker Compose | Inicialização reproduzível dos serviços |

## Equipe

| Nome                              | Papel no pipeline de dados                              |
| --------------------------------- | ------------------------------------------------------- |
| Lucas Macedo Barboza              | Integrante                                              |
| Caetano Santos Lucio              | Engenharia de dados, embeddings e runtime do assistente |
| Cairo Florenço                    | Integrante                                              |
| Leonardo Sobrinho                 | Integrante                                              |
| Carlos Eduardo Mendes de Mesquita | Integrante                                              |
| Bruna                             | Integrante                                              |
| Lais                              | Integrante                                              |


## Executar o projeto

Requisitos: Docker com Docker Compose e acesso à internet.

```bash
cp .env.example .env
docker compose up --build
```

Depois da inicialização, abra:

- aplicação: <http://localhost:8000>;
- documentação da API: <http://localhost:8000/docs>.

## Documentação

A documentação completa do projeto, das entregas da disciplina e das decisões de modelagem está no [GitHub Pages do GuiaOrientador-UnB](https://ca1ro.github.io/GuiaTCC-UnB/).

Para visualizar o site localmente:

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
