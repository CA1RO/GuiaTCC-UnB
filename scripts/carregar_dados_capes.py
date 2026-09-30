"""Carga idempotente dos docentes de pós-graduação da UnB publicados pela CAPES.

Uso padrão (baixa a fonte pública configurada):
    python -m scripts.carregar_dados_capes

Uso com um arquivo já disponível, útil para testes:
    python -m scripts.carregar_dados_capes --arquivo /caminho/docentes.csv
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.models import Docente, DocentePrograma, ProgramaPosGraduacao
from src.db.session import async_session
from src.pipeline.capes import baixar_csv, consolidar_registros, iterar_registros


logger = logging.getLogger(__name__)
TAMANHO_LOTE = 500


def _lotes(linhas: list[dict], tamanho: int = TAMANHO_LOTE):
    for inicio in range(0, len(linhas), tamanho):
        yield linhas[inicio : inicio + tamanho]


async def _upsert_programas(db: AsyncSession, linhas: list[dict]) -> None:
    for lote in _lotes(linhas):
        comando = insert(ProgramaPosGraduacao).values(lote)
        await db.execute(
            comando.on_conflict_do_update(
                index_elements=[ProgramaPosGraduacao.codigo_capes],
                set_={
                    "nome": comando.excluded.nome,
                    "grau": comando.excluded.grau,
                    "modalidade": comando.excluded.modalidade,
                    "conceito": comando.excluded.conceito,
                    "area_avaliacao": comando.excluded.area_avaliacao,
                    "grande_area_conhecimento": comando.excluded.grande_area_conhecimento,
                    "area_conhecimento": comando.excluded.area_conhecimento,
                    "municipio": comando.excluded.municipio,
                    "uf": comando.excluded.uf,
                },
            )
        )


async def _upsert_docentes(db: AsyncSession, linhas: list[dict]) -> None:
    for lote in _lotes(linhas):
        comando = insert(Docente).values(lote)
        await db.execute(
            comando.on_conflict_do_update(
                index_elements=[Docente.id_capes],
                set_={
                    "nome": comando.excluded.nome,
                    "titulacao": comando.excluded.titulacao,
                    "ano_titulacao": comando.excluded.ano_titulacao,
                    "area_titulacao": comando.excluded.area_titulacao,
                    "tipo_vinculo": comando.excluded.tipo_vinculo,
                    "regime_trabalho": comando.excluded.regime_trabalho,
                    "situacao": comando.excluded.situacao,
                    "data_atualizacao": comando.excluded.data_atualizacao,
                },
            )
        )


async def _upsert_vinculos(db: AsyncSession, linhas: list[dict]) -> None:
    for lote in _lotes(linhas):
        comando = insert(DocentePrograma).values(lote)
        await db.execute(
            comando.on_conflict_do_update(
                index_elements=[
                    DocentePrograma.id_docente,
                    DocentePrograma.id_programa,
                    DocentePrograma.ano_base,
                ],
                set_={"categoria_docente": comando.excluded.categoria_docente},
            )
        )


async def carregar(arquivo: Path) -> dict[str, int]:
    docentes, programas, vinculos = consolidar_registros(
        iterar_registros(arquivo, settings.capes_sigla_instituicao)
    )
    if not docentes:
        raise RuntimeError(
            f"Nenhum registro encontrado para {settings.capes_sigla_instituicao}."
        )

    linhas_programas = [
        {
            "codigo_capes": registro.codigo_programa,
            "nome": registro.nome_programa,
            "grau": registro.grau_programa,
            "modalidade": registro.modalidade_programa,
            "conceito": registro.conceito_programa,
            "area_avaliacao": registro.area_avaliacao,
            "grande_area_conhecimento": registro.grande_area_conhecimento,
            "area_conhecimento": registro.area_conhecimento,
            "municipio": registro.municipio_programa,
            "uf": registro.uf_programa,
        }
        for registro in programas.values()
    ]
    linhas_docentes = [
        {
            "id_capes": registro.id_pessoa,
            "nome": registro.nome_docente,
            "titulacao": registro.titulacao,
            "ano_titulacao": registro.ano_titulacao,
            "area_titulacao": registro.area_titulacao,
            "tipo_vinculo": registro.tipo_vinculo,
            "regime_trabalho": registro.regime_trabalho,
            "situacao": "ativo",
        }
        for registro in docentes.values()
    ]

    async with async_session() as db:
        try:
            await _upsert_programas(db, linhas_programas)
            await _upsert_docentes(db, linhas_docentes)

            resultado_docentes = await db.execute(
                select(Docente.id_capes, Docente.id_docente).where(
                    Docente.id_capes.in_(docentes)
                )
            )
            ids_docentes = dict(resultado_docentes.all())

            resultado_programas = await db.execute(
                select(ProgramaPosGraduacao.codigo_capes, ProgramaPosGraduacao.id_programa).where(
                    ProgramaPosGraduacao.codigo_capes.in_(programas)
                )
            )
            ids_programas = dict(resultado_programas.all())

            linhas_vinculos = [
                {
                    "id_docente": ids_docentes[registro.id_pessoa],
                    "id_programa": ids_programas[registro.codigo_programa],
                    "ano_base": registro.ano_base,
                    "categoria_docente": registro.categoria_docente,
                }
                for registro in vinculos
            ]
            await _upsert_vinculos(db, linhas_vinculos)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    return {
        "docentes": len(docentes),
        "programas": len(programas),
        "vinculos": len(vinculos),
    }


async def executar(arquivo_informado: Path | None) -> None:
    if arquivo_informado:
        estatisticas = await carregar(arquivo_informado)
    else:
        with TemporaryDirectory(prefix="guia_capes_") as diretorio:
            arquivo = Path(diretorio) / "docentes_capes.csv"
            logger.info("Baixando fonte pública da CAPES")
            baixar_csv(settings.capes_docentes_url, arquivo)
            estatisticas = await carregar(arquivo)

    logger.info(
        "Carga concluída: %d docentes, %d programas e %d vínculos",
        estatisticas["docentes"],
        estatisticas["programas"],
        estatisticas["vinculos"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arquivo", type=Path, help="CSV local da CAPES")
    argumentos = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    asyncio.run(executar(argumentos.arquivo))


if __name__ == "__main__":
    main()
