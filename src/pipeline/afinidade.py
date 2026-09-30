"""Busca por afinidade: projeto primeiro, docente só se não houver projeto."""

import re

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Departamento, Docente, ProjetoPesquisa

LIMIAR = 0.68
TIPOS = ("pesquisa", "extensao", "tcc")
ROTULOS = {"pesquisa": "Pesquisa", "extensao": "Extensão", "tcc": "TCC"}

_STOPWORDS = {
    "quero", "trabalhar", "com", "alguem", "alguém", "para", "sobre", "quem",
    "pesquisa", "pesquisam", "uma", "uns", "das", "dos", "que", "por", "como",
    "meu", "minha", "tema", "orientador", "orientadora", "projeto", "projetos",
    "extensao", "extensão", "estudar", "estudo", "gostaria", "interesse",
    "afinidade", "linha", "area", "área", "curso", "encontrar", "achar",
}


def termos_da_busca(texto: str) -> list[str]:
    termos = [
        termo
        for termo in re.findall(r"[0-9a-záàâãéêíóôõúç]+", texto.lower())
        if len(termo) > 3 and termo not in _STOPWORDS
    ]
    return termos or [texto.strip()]


def _pontuacao(termos: list[str], corpus):
    notas = [func.word_similarity(termo, corpus) for termo in termos]
    soma = notas[0]
    for nota in notas[1:]:
        soma = soma + nota
    return soma / float(len(notas))


def _projeto_dict(projeto: ProjetoPesquisa, docente: Docente, departamento: Departamento | None, similaridade: float | None) -> dict:
    return {
        "id_projeto": projeto.id_projeto,
        "titulo": projeto.titulo,
        "descricao": projeto.descricao,
        "tipo": projeto.tipo,
        "status": projeto.status,
        "palavras_chave": projeto.palavras_chave,
        "ano_inicio": projeto.ano_inicio,
        "id_docente": docente.id_docente,
        "nome_docente": docente.nome,
        "email_docente": docente.email,
        "titulacao": docente.titulacao,
        "departamento_nome": departamento.nome if departamento else None,
        "departamento_sigla": departamento.sigla if departamento else None,
        "similaridade": similaridade,
    }


def _docente_dict(docente: Docente, departamento: Departamento | None, similaridade: float | None) -> dict:
    return {
        "id_docente": docente.id_docente,
        "nome": docente.nome,
        "email": docente.email,
        "titulacao": docente.titulacao,
        "linha_pesquisa": docente.linha_pesquisa,
        "departamento_nome": departamento.nome if departamento else None,
        "departamento_sigla": departamento.sigla if departamento else None,
        "similaridade": similaridade,
    }


async def buscar_afinidade(
    db: AsyncSession,
    termo: str = "",
    tipo: str | None = None,
    departamento: str | None = None,
    limite: int = 12,
) -> dict:
    """Devolve projetos alinhados. Sem projeto, devolve docentes com linha parecida."""
    corpus = func.concat_ws(
        " ",
        ProjetoPesquisa.titulo,
        func.coalesce(ProjetoPesquisa.descricao, ""),
        func.coalesce(func.array_to_string(ProjetoPesquisa.palavras_chave, " "), ""),
        Docente.nome,
    )
    consulta = (
        select(ProjetoPesquisa, Docente, Departamento)
        .join(Docente, ProjetoPesquisa.id_docente == Docente.id_docente)
        .outerjoin(Departamento, Docente.id_departamento == Departamento.id_departamento)
        .where(ProjetoPesquisa.status == "ativo")
    )
    if tipo in TIPOS:
        consulta = consulta.where(ProjetoPesquisa.tipo == tipo)
    if departamento:
        consulta = consulta.where(Departamento.nome.ilike(f"%{departamento}%"))

    texto = termo.strip()
    if texto:
        score = _pontuacao(termos_da_busca(texto), corpus)
        consulta = consulta.add_columns(score.label("similaridade")).where(score > LIMIAR).order_by(desc(score))
    else:
        consulta = consulta.order_by(ProjetoPesquisa.titulo)

    linhas = (await db.execute(consulta.limit(limite))).all()
    projetos = [
        _projeto_dict(
            linha.ProjetoPesquisa,
            linha.Docente,
            linha.Departamento,
            float(linha.similaridade) if texto else None,
        )
        for linha in linhas
    ]
    if projetos or not texto:
        return {"modo": "projetos", "projetos": projetos, "docentes": []}

    linha_docente = func.coalesce(Docente.linha_pesquisa, "")
    score_docente = _pontuacao(termos_da_busca(texto), linha_docente)
    consulta_docente = (
        select(Docente, Departamento, score_docente.label("similaridade"))
        .outerjoin(Departamento, Docente.id_departamento == Departamento.id_departamento)
        .where(Docente.linha_pesquisa.is_not(None), score_docente > LIMIAR)
        .order_by(desc(score_docente))
        .limit(limite)
    )
    if departamento:
        consulta_docente = consulta_docente.where(Departamento.nome.ilike(f"%{departamento}%"))

    docentes = [
        _docente_dict(linha.Docente, linha.Departamento, float(linha.similaridade))
        for linha in (await db.execute(consulta_docente)).all()
    ]
    return {"modo": "docentes", "projetos": [], "docentes": docentes}
