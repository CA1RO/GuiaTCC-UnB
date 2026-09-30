# GuiaOrientador-UnB

## Um ponto de partida para encontrar temas e orientação acadêmica na UnB

O **GuiaOrientador-UnB** é uma plataforma de apoio à escolha de temas e orientadores de trabalhos acadêmicos na Universidade de Brasília. O projeto organiza informações acadêmicas para ajudar estudantes a descobrir docentes, programas e áreas relacionados aos assuntos que pretendem desenvolver.

## Problema

Estudantes que estão iniciando um TCC, uma monografia ou uma atividade de iniciação científica nem sempre sabem quais docentes atuam na área que desejam pesquisar. As informações existem, mas costumam estar distribuídas entre departamentos, programas de pós-graduação, currículos e portais institucionais.

Essa dispersão faz com que a escolha de um tema ou orientador dependa, muitas vezes, do conhecimento informal sobre quem pesquisa determinado assunto dentro da universidade.

## Proposta

O GuiaOrientador reúne e estrutura dados acadêmicos públicos para aproximar três elementos:

1. o tema ou a área de interesse do estudante;
2. os docentes que atuam em áreas relacionadas;
3. os programas e contextos acadêmicos nos quais esses docentes trabalham.

O objetivo é oferecer um ponto de partida confiável para que a busca por orientação seja mais informada, reproduzível e menos dependente de contatos prévios dentro da universidade.

## Público

O público principal são estudantes da UnB que estejam:

- definindo um tema de TCC ou monografia;
- procurando orientação acadêmica;
- buscando oportunidades de PIBIC ou PIBITI;
- explorando áreas de pesquisa fora do próprio departamento.

## Como o projeto funciona

1. Dados acadêmicos públicos são obtidos de fontes oficiais.
2. A pipeline seleciona os campos necessários, normaliza os registros e evita duplicações.
3. As informações são armazenadas em um banco relacional versionado por migrações.
4. A API disponibiliza os dados para a interface e para os módulos de busca.
5. O estudante informa um tema ou uma área de interesse.
6. A plataforma apresenta docentes, programas e áreas relacionados à consulta.

## Pipeline de dados

```text
Fonte pública -> Ingestão -> Transformação -> Validação -> Banco -> API -> Interface
```

A pipeline foi projetada para permitir cargas reproduzíveis e idempotentes. Isso significa que o ambiente pode ser reconstruído a partir de um banco vazio e que a repetição de uma carga não deve criar registros duplicados.

Todos os integrantes participam das etapas de escolha das fontes, modelagem, implementação, validação, documentação e revisão.

## Arquitetura

O GuiaOrientador é organizado em serviços independentes executados pelo Docker Compose.

```text
Fontes públicas
      |
      v
Pipeline de dados ---> PostgreSQL + pgvector
                            |
                            v
                         FastAPI
                            |
                            v
                         Frontend
```

### Componentes

| Componente | Responsabilidade |
| --- | --- |
| Frontend | Interface de consulta e interação com o estudante |
| FastAPI | API, validações e regras da aplicação |
| PostgreSQL | Dados relacionais do domínio |
| pgvector | Estrutura para evolução da busca por similaridade |
| Redis | Cache e apoio às sessões da aplicação |
| SeaweedFS | Armazenamento de objetos compatível com S3 |
| Alembic | Versionamento do esquema físico |
| Pipeline de dados | Download, transformação, validação e carga das fontes |

### Princípios

- ambiente reproduzível a partir de um banco vazio;
- esquema versionado por migrações;
- carga automática e idempotente;
- separação entre fonte pública, banco e aplicação;
- documentação coerente com o comportamento executável do repositório.

## Tecnologias principais

- Python e FastAPI;
- PostgreSQL e pgvector;
- Alembic;
- Redis;
- SeaweedFS;
- Docker Compose;
- MkDocs Material.

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

Depois da inicialização:

- aplicação: <http://localhost:8000>;
- documentação da API: <http://localhost:8000/docs>.

## Entregas da disciplina

Os requisitos, medições e decisões específicas de cada entrega ficam separados da apresentação geral do projeto. A aba **Entrega 1** reúne a documentação da fonte pública, do esquema físico, das migrações, da carga e da decisão de modelagem.

O código-fonte está disponível no [repositório do projeto](https://github.com/CA1RO/GuiaTCC-UnB).
