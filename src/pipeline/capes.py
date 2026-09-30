"""Leitura da fonte pública de docentes da pós-graduação da CAPES."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


CAMPOS_OBRIGATORIOS = {
    "AN_BASE",
    "SG_ENTIDADE_ENSINO",
    "ID_PESSOA",
    "NM_DOCENTE",
    "CD_PROGRAMA_IES",
    "NM_PROGRAMA_IES",
}


@dataclass(frozen=True)
class RegistroCapes:
    """Recorte dos campos da CAPES usados pela fonte OLTP."""

    ano_base: int
    id_pessoa: int
    nome_docente: str
    titulacao: str | None
    ano_titulacao: int | None
    area_titulacao: str | None
    tipo_vinculo: str | None
    regime_trabalho: str | None
    categoria_docente: str | None
    codigo_programa: str
    nome_programa: str
    grau_programa: str | None
    modalidade_programa: str | None
    conceito_programa: str | None
    area_avaliacao: str | None
    grande_area_conhecimento: str | None
    area_conhecimento: str | None
    municipio_programa: str | None
    uf_programa: str | None


def _texto(valor: str | None) -> str | None:
    if valor is None:
        return None
    limpo = valor.strip()
    if not limpo or limpo.upper() in {"NA", "N/A", "NULL"}:
        return None
    return limpo


def _inteiro(valor: str | None) -> int | None:
    texto = _texto(valor)
    return int(texto) if texto else None


def baixar_csv(url: str, destino: Path, tamanho_bloco: int = 1024 * 1024) -> Path:
    """Baixa o CSV em fluxo para não manter o arquivo nacional em memória."""
    import requests

    with requests.get(url, stream=True, timeout=(15, 180)) as resposta:
        resposta.raise_for_status()
        with destino.open("wb") as arquivo:
            for bloco in resposta.iter_content(chunk_size=tamanho_bloco):
                if bloco:
                    arquivo.write(bloco)
    return destino


def iterar_registros(caminho: Path, sigla_instituicao: str = "UNB") -> Iterator[RegistroCapes]:
    """Lê o CSV nacional e entrega somente vínculos da instituição escolhida."""
    with caminho.open(encoding="latin-1", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";")
        ausentes = CAMPOS_OBRIGATORIOS - set(leitor.fieldnames or [])
        if ausentes:
            nomes = ", ".join(sorted(ausentes))
            raise ValueError(f"CSV da CAPES sem campos obrigatórios: {nomes}")

        for linha in leitor:
            if linha["SG_ENTIDADE_ENSINO"].strip().upper() != sigla_instituicao.upper():
                continue

            yield RegistroCapes(
                ano_base=int(linha["AN_BASE"]),
                id_pessoa=int(linha["ID_PESSOA"]),
                nome_docente=linha["NM_DOCENTE"].strip(),
                titulacao=_texto(linha.get("NM_GRAU_TITULACAO")),
                ano_titulacao=_inteiro(linha.get("AN_TITULACAO")),
                area_titulacao=_texto(linha.get("NM_AREA_BASICA_TITULACAO")),
                tipo_vinculo=_texto(linha.get("DS_TIPO_VINCULO_DOCENTE_IES")),
                regime_trabalho=_texto(linha.get("DS_REGIME_TRABALHO")),
                categoria_docente=_texto(linha.get("DS_CATEGORIA_DOCENTE")),
                codigo_programa=linha["CD_PROGRAMA_IES"].strip(),
                nome_programa=linha["NM_PROGRAMA_IES"].strip(),
                grau_programa=_texto(linha.get("NM_GRAU_PROGRAMA")),
                modalidade_programa=_texto(linha.get("NM_MODALIDADE_PROGRAMA")),
                conceito_programa=_texto(linha.get("CD_CONCEITO_PROGRAMA")),
                area_avaliacao=_texto(linha.get("NM_AREA_AVALIACAO")),
                grande_area_conhecimento=_texto(linha.get("NM_GRANDE_AREA_CONHECIMENTO")),
                area_conhecimento=_texto(linha.get("NM_AREA_CONHECIMENTO")),
                municipio_programa=_texto(linha.get("NM_MUNICIPIO_PROGRAMA_IES")),
                uf_programa=_texto(linha.get("SG_UF_PROGRAMA")),
            )


def consolidar_registros(
    registros: Iterator[RegistroCapes],
) -> tuple[dict[int, RegistroCapes], dict[str, RegistroCapes], list[RegistroCapes]]:
    """Deduplica entidades, preservando um vínculo por docente/programa/ano."""
    docentes: dict[int, RegistroCapes] = {}
    programas: dict[str, RegistroCapes] = {}
    vinculos: dict[tuple[int, str, int], RegistroCapes] = {}

    for registro in registros:
        docentes[registro.id_pessoa] = registro
        programas[registro.codigo_programa] = registro
        chave_vinculo = (registro.id_pessoa, registro.codigo_programa, registro.ano_base)
        vinculos[chave_vinculo] = registro

    return docentes, programas, list(vinculos.values())
