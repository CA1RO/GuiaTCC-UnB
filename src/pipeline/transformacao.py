"""
Etapa 2 do Pipeline — Parsing, Limpeza e Normalização (Bronze → Silver)

Responsável por:
- Extração de nós XML de currículos Lattes
- Limpeza de tags HTML, normalização de nomes
- Deduplicação de artigos entre coautores
- Geração de Parquet particionado (camada Silver)

Ferramentas: DuckDB + PyArrow + Pandas
Frequência: Semanal (domingos às 04h).
Conforme aba "5 Pipeline", linha 2.
"""

import logging
import re
import unicodedata

import duckdb
import pandas as pd
from lxml import etree

logger = logging.getLogger(__name__)


def normalizar_nome(nome: str) -> str:
    """Remove acentos, normaliza espaçamentos e capitaliza."""
    nome = unicodedata.normalize("NFKD", nome)
    nome = nome.encode("ascii", "ignore").decode("ascii")
    nome = re.sub(r"\s+", " ", nome).strip()
    return nome.title()


def limpar_html(texto: str) -> str:
    """Remove tags HTML/XML residuais de textos."""
    if not texto:
        return ""
    clean = re.sub(r"<[^>]+>", "", texto)
    return re.sub(r"\s+", " ", clean).strip()


def parsear_curriculo_lattes(xml_bytes: bytes) -> dict:
    """
    Extrai dados estruturados de um currículo Lattes em XML.

    Returns:
        Dicionário com dados do docente, projetos e produções.
    """
    tree = etree.fromstring(xml_bytes)

    dados_gerais = tree.find(".//DADOS-GERAIS")
    if dados_gerais is None:
        logger.warning("XML sem DADOS-GERAIS")
        return {}

    nome = dados_gerais.get("NOME-COMPLETO", "")
    resumo_cv = tree.find(".//RESUMO-CV")
    texto_resumo = resumo_cv.get("TEXTO-RESUMO-CV-RH", "") if resumo_cv is not None else ""

    areas = []
    for area in tree.findall(".//AREA-DE-ATUACAO"):
        areas.append({
            "grande_area": area.get("NOME-GRANDE-AREA-DO-CONHECIMENTO", ""),
            "area": area.get("NOME-DA-AREA-DO-CONHECIMENTO", ""),
            "sub_area": area.get("NOME-DA-SUB-AREA-DO-CONHECIMENTO", ""),
            "especialidade": area.get("NOME-DA-ESPECIALIDADE", ""),
        })

    projetos = []
    for proj in tree.findall(".//PROJETO-DE-PESQUISA"):
        projetos.append({
            "titulo": proj.get("NOME-DO-PROJETO", ""),
            "descricao": limpar_html(proj.get("DESCRICAO-DO-PROJETO", "")),
            "ano_inicio": proj.get("ANO-INICIO", ""),
            "ano_fim": proj.get("ANO-FIM", ""),
            "situacao": proj.get("SITUACAO", ""),
        })

    artigos = []
    for artigo in tree.findall(".//ARTIGO-PUBLICADO"):
        dados = artigo.find("DADOS-BASICOS-DO-ARTIGO")
        if dados is not None:
            artigos.append({
                "titulo": dados.get("TITULO-DO-ARTIGO", ""),
                "ano": dados.get("ANO-DO-ARTIGO", ""),
                "idioma": dados.get("IDIOMA", ""),
            })

    return {
        "nome": normalizar_nome(nome),
        "resumo": limpar_html(texto_resumo),
        "areas_atuacao": areas,
        "projetos": projetos,
        "artigos": artigos,
    }


def transformar_para_silver(dados_docentes: list[dict], output_path: str) -> str:
    """
    Transforma dados parseados em Parquet particionado (Silver).

    Args:
        dados_docentes: Lista de dicts resultantes do parsing.
        output_path: Caminho para salvar o Parquet.

    Returns:
        Caminho do arquivo gerado.
    """
    df = pd.DataFrame(dados_docentes)

    con = duckdb.connect()
    con.register("docentes_raw", df)

    df_limpo = con.execute("""
        SELECT DISTINCT
            nome,
            resumo,
            areas_atuacao,
            projetos,
            artigos
        FROM docentes_raw
        WHERE nome IS NOT NULL AND nome != ''
    """).fetchdf()

    df_limpo.to_parquet(output_path, engine="pyarrow", index=False)
    logger.info(f"Silver Parquet gerado: {output_path} ({len(df_limpo)} registros)")
    return output_path
