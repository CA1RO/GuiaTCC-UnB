"""
Script de seed — popula o banco com dados de exemplo para desenvolvimento.

Uso:
    python -m scripts.seed_dados_exemplo

Cria departamentos, docentes e projetos fictícios para testes locais.
"""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Departamento, Docente, ProjetoPesquisa
from src.db.session import async_session


DEPARTAMENTOS = [
    {"nome": "Departamento de Ciência da Computação", "sigla": "CIC", "faculdade": "Instituto de Ciências Exatas"},
    {"nome": "Departamento de Engenharia Elétrica", "sigla": "ENE", "faculdade": "Faculdade de Tecnologia"},
    {"nome": "Departamento de Matemática", "sigla": "MAT", "faculdade": "Instituto de Ciências Exatas"},
    {"nome": "Departamento de Estatística", "sigla": "EST", "faculdade": "Instituto de Ciências Exatas"},
    {"nome": "Faculdade de Comunicação", "sigla": "FAC", "faculdade": "Faculdade de Comunicação"},
]

DOCENTES = [
    {
        "nome": "Maria Silva Santos",
        "email": "maria.silva@unb.br",
        "titulacao": "Doutora",
        "id_lattes": "1234567890",
        "departamento_sigla": "CIC",
        "linha_pesquisa": "Processamento de linguagem natural e sistemas de recomendação.",
        "projetos": [
            {
                "titulo": "Modelos de Linguagem para Processamento de Texto em Português",
                "descricao": "Pesquisa sobre adaptação de LLMs para tarefas de NLP em português brasileiro.",
                "tipo": "pesquisa",
                "ano_inicio": 2023,
                "status": "ativo",
                "palavras_chave": ["NLP", "LLM", "português", "transformers"],
            },
            {
                "titulo": "Oficinas de linguagem simples para a comunidade acadêmica",
                "descricao": "Extensão que traduz artigos e resumos de pesquisa para estudantes de início de curso.",
                "tipo": "extensao",
                "ano_inicio": 2024,
                "status": "ativo",
                "palavras_chave": ["extensão", "linguagem simples", "divulgação"],
            },
        ],
    },
    {
        "nome": "João Pedro Oliveira",
        "email": "joao.oliveira@unb.br",
        "titulacao": "Doutor",
        "id_lattes": "0987654321",
        "departamento_sigla": "CIC",
        "linha_pesquisa": "Segurança de sistemas distribuídos e blockchain.",
        "projetos": [
            {
                "titulo": "Segurança em Sistemas Distribuídos com Blockchain",
                "descricao": "Estudo de mecanismos de consenso e segurança em redes blockchain.",
                "tipo": "pesquisa",
                "ano_inicio": 2024,
                "status": "ativo",
                "palavras_chave": ["blockchain", "segurança", "sistemas distribuídos"],
            },
        ],
    },
    {
        "nome": "Ana Carolina Ferreira",
        "email": "ana.ferreira@unb.br",
        "titulacao": "Doutora",
        "id_lattes": "1122334455",
        "departamento_sigla": "ENE",
        "linha_pesquisa": "Visão computacional e aprendizado profundo.",
        "projetos": [
            {
                "titulo": "Visão Computacional aplicada a Veículos Autônomos",
                "descricao": "Pesquisa em percepção visual para navegação autônoma usando deep learning.",
                "tipo": "pesquisa",
                "ano_inicio": 2023,
                "status": "ativo",
                "palavras_chave": ["visão computacional", "deep learning", "veículos autônomos"],
            },
            {
                "titulo": "Classificação de imagens para apoio ao diagnóstico",
                "descricao": "Vaga de TCC para comparar modelos de visão computacional em exames de imagem.",
                "tipo": "tcc",
                "ano_inicio": 2026,
                "status": "ativo",
                "palavras_chave": ["TCC", "imagens médicas", "visão computacional"],
            },
        ],
    },
    {
        "nome": "Carlos Roberto Lima",
        "email": "carlos.lima@unb.br",
        "titulacao": "Doutor",
        "id_lattes": "5566778899",
        "departamento_sigla": "MAT",
        "linha_pesquisa": "Otimização combinatória e pesquisa operacional.",
        "projetos": [
            {
                "titulo": "Otimização Combinatória aplicada a Problemas de Logística",
                "descricao": "Modelos matemáticos para otimização de rotas e alocação de recursos.",
                "tipo": "pesquisa",
                "ano_inicio": 2022,
                "status": "ativo",
                "palavras_chave": ["otimização", "logística", "programação linear"],
            },
        ],
    },
    {
        "nome": "Helena Costa Ribeiro",
        "email": "helena.ribeiro@unb.br",
        "titulacao": "Doutora",
        "id_lattes": "6677889900",
        "departamento_sigla": "MAT",
        "linha_pesquisa": "Álgebra linear, ensino de matemática e formação de professores.",
        "projetos": [],
    },
]


async def seed():
    async with async_session() as db:
        # Departamentos
        deps_map = {}
        for dep_data in DEPARTAMENTOS:
            dep = Departamento(**dep_data)
            db.add(dep)
            await db.flush()
            deps_map[dep_data["sigla"]] = dep.id_departamento

        # Docentes e projetos
        for doc_data in DOCENTES:
            projetos_data = doc_data.pop("projetos")
            sigla = doc_data.pop("departamento_sigla")
            doc_data["id_departamento"] = deps_map[sigla]

            docente = Docente(**doc_data)
            db.add(docente)
            await db.flush()

            for proj_data in projetos_data:
                projeto = ProjetoPesquisa(id_docente=docente.id_docente, **proj_data)
                db.add(projeto)

        await db.commit()
        print(f"✓ Seed concluído: {len(DEPARTAMENTOS)} departamentos, {len(DOCENTES)} docentes")


if __name__ == "__main__":
    asyncio.run(seed())
