"""
Carga reprodutível da fonte pública de docentes da UnB.

Baixa o pacote publicado no CKAN, grava o bruto no bucket bronze e faz
upsert de departamento e docente. Não grava salário. Pode rodar de novo:
a segunda execução atualiza a lotação e a situação, sem duplicar nome.

    docker compose exec api python -m scripts.carregar_dados_abertos
"""

import asyncio
import csv
import io
import logging
import tempfile
from datetime import datetime
from pathlib import Path

import httpx
import py7zr
from sqlalchemy import text

from src.db.session import async_session
from src.pipeline.ingestao import garantir_buckets, ingerir_dados_abertos_unb

logger = logging.getLogger(__name__)

URL = (
    "https://dados.unb.br/dataset/9b6891b9-3c87-4337-b1d7-6c4187b10d00"
    "/resource/4cf8c882-82ea-4a19-a775-3f062cd1cc62"
    "/download/dados_institucionais_docentes.7z"
)
MIGRACAO = (
    Path(__file__).resolve().parents[1] / "db" / "migrations" / "0002_docente_origem.sql"
)


def _limpa(valor: str | None) -> str:
    return " ".join((valor or "").split())


def _data(valor: str | None):
    texto = _limpa(valor)
    if not texto or texto == "0":
        return None
    return datetime.strptime(texto, "%d/%m/%Y").date()


def ler_docentes(arquivo: bytes) -> list[dict]:
    with tempfile.TemporaryDirectory() as pasta:
        with py7zr.SevenZipFile(io.BytesIO(arquivo)) as pacote:
            pacote.extractall(path=pasta)
        csv_path = next(Path(pasta).rglob("*.csv"))
        texto = csv_path.read_text(encoding="latin-1")
    linhas = csv.DictReader(io.StringIO(texto), delimiter=";")
    registros = []
    for linha in linhas:
        nome = _limpa(linha["nome_serv"])
        unidade = _limpa(linha["uorg_lotacao"])
        if not nome or not unidade:
            continue
        registros.append(
            {
                "nome": nome,
                "titulacao": _limpa(linha["tipo_prof"]) or None,
                "situacao": _limpa(linha["reg_jur"]) or None,
                "departamento_nome": unidade,
                "departamento_sigla": _limpa(linha["sigla_uorg_lotacao"]) or None,
                "faculdade": _limpa(linha["denom_uorg_pai_lotacao"]) or None,
                "data_ingresso_orgao": _data(linha["data_ingres_orgao"]),
                "data_lotacao": _data(linha["data_lotacao"]),
            }
        )
    return registros


async def carregar(registros: list[dict]) -> dict:
    async with async_session() as session:
        for comando in MIGRACAO.read_text(encoding="utf-8").split(";"):
            if comando.strip():
                await session.execute(text(comando))

        unidades = {}
        for registro in registros:
            unidades[registro["departamento_nome"]] = {
                "nome": registro["departamento_nome"],
                "sigla": registro["departamento_sigla"],
                "faculdade": registro["faculdade"],
            }
        await session.execute(
            text(
                """
                INSERT INTO departamento (nome, sigla, faculdade)
                VALUES (:nome, :sigla, :faculdade)
                ON CONFLICT (nome) DO UPDATE
                SET sigla = EXCLUDED.sigla,
                    faculdade = EXCLUDED.faculdade
                """
            ),
            list(unidades.values()),
        )
        ids = {
            nome: id_departamento
            for id_departamento, nome in (
                await session.execute(text("SELECT id_departamento, nome FROM departamento"))
            ).all()
        }
        docentes = [
            {
                "nome": registro["nome"],
                "titulacao": registro["titulacao"],
                "situacao": registro["situacao"],
                "id_departamento": ids[registro["departamento_nome"]],
                "data_ingresso_orgao": registro["data_ingresso_orgao"],
                "data_lotacao": registro["data_lotacao"],
            }
            for registro in registros
        ]
        await session.execute(
            text(
                """
                INSERT INTO docente (
                    nome, titulacao, situacao, id_departamento,
                    data_ingresso_orgao, data_lotacao, data_atualizacao
                )
                VALUES (
                    :nome, :titulacao, :situacao, :id_departamento,
                    :data_ingresso_orgao, :data_lotacao, NOW()
                )
                ON CONFLICT (nome) DO UPDATE
                SET titulacao = EXCLUDED.titulacao,
                    situacao = EXCLUDED.situacao,
                    id_departamento = EXCLUDED.id_departamento,
                    data_ingresso_orgao = EXCLUDED.data_ingresso_orgao,
                    data_lotacao = EXCLUDED.data_lotacao,
                    data_atualizacao = NOW()
                """
            ),
            docentes,
        )
        totais = (
            await session.execute(
                text(
                    """
                    SELECT
                        (SELECT count(*) FROM departamento) AS departamentos,
                        (SELECT count(*) FROM docente) AS docentes,
                        (SELECT count(*) FROM docente WHERE situacao = 'ATIVO PERMANENTE') AS ativos
                    """
                )
            )
        ).one()
        await session.commit()
    return {
        "lidos": len(registros),
        "departamentos": totais.departamentos,
        "docentes": totais.docentes,
        "ativos_permanentes": totais.ativos,
    }


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as cliente:
        resposta = await cliente.get(URL)
        resposta.raise_for_status()
        arquivo = resposta.content
    logger.info("Arquivo baixado: %s bytes", len(arquivo))

    try:
        garantir_buckets()
        bruto = ingerir_dados_abertos_unb(URL, "dados_institucionais_docentes.7z")
        logger.info("Bronze: %s", bruto["object_name"])
    except Exception as erro:
        logger.warning("Bronze não gravado (%s). A carga relacional segue.", erro)

    registros = ler_docentes(arquivo)
    totais = await carregar(registros)
    logger.info(
        "Carga concluída: %s linhas lidas, %s docentes, %s departamentos, %s ativos permanentes.",
        totais["lidos"],
        totais["docentes"],
        totais["departamentos"],
        totais["ativos_permanentes"],
    )


if __name__ == "__main__":
    asyncio.run(main())
