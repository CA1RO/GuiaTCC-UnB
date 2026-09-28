"""
Medição da modelagem da origem, com o dado público já carregado.

Compara a tabela atual (CRUD, um registro por docente) com uma cópia
insert-only de dois recortes semanais da mesma fonte. A consulta é a
pergunta de gestão: quantos docentes ativos permanentes há por unidade.

    docker compose exec api python -m scripts.medir_modelagem_origem
"""

import asyncio

from sqlalchemy import text

from src.db.session import async_session

CONSULTA_CRUD = """
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT departamento.sigla, count(*) AS ativos
FROM docente
JOIN departamento ON departamento.id_departamento = docente.id_departamento
WHERE docente.situacao = 'ATIVO PERMANENTE'
GROUP BY departamento.sigla
"""

CONSULTA_INSERT_ONLY = """
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT departamento.sigla, count(*) AS ativos
FROM docente_recorte
JOIN departamento ON departamento.id_departamento = docente_recorte.id_departamento
WHERE docente_recorte.situacao = 'ATIVO PERMANENTE'
  AND docente_recorte.carregado_em = (
      SELECT max(carregado_em) FROM docente_recorte
  )
GROUP BY departamento.sigla
"""

BUSCA_NOME = """
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id_docente, nome
FROM docente
WHERE nome = 'ABIMAEL DE JESUS BARROS COSTA'
"""


def _tempo(plano: list[str]) -> str:
    for linha in plano:
        if "Execution Time" in linha:
            return linha.split("Execution Time:")[-1].strip()
    return "sem tempo"


async def main() -> None:
    async with async_session() as session:
        await session.execute(text("DROP TABLE IF EXISTS docente_recorte"))
        await session.execute(
            text(
                """
                CREATE TEMP TABLE docente_recorte AS
                SELECT docente.*, NOW() - INTERVAL '7 days' AS carregado_em
                FROM docente
                WHERE data_ingresso_orgao IS NOT NULL
                UNION ALL
                SELECT docente.*, NOW() AS carregado_em
                FROM docente
                WHERE data_ingresso_orgao IS NOT NULL
                """
            )
        )
        await session.execute(
            text("CREATE INDEX ON docente_recorte (carregado_em, situacao)")
        )
        tamanhos = (
            await session.execute(
                text(
                    """
                    SELECT
                        (SELECT count(*) FROM docente) AS docentes,
                        (SELECT count(*) FROM docente_recorte) AS recortes,
                        pg_size_pretty(pg_total_relation_size('docente')) AS tamanho_docente,
                        pg_size_pretty(pg_total_relation_size('docente_recorte')) AS tamanho_recorte
                    """
                )
            )
        ).one()
        crud = [linha[0] for linha in (await session.execute(text(CONSULTA_CRUD))).all()]
        historico = [
            linha[0] for linha in (await session.execute(text(CONSULTA_INSERT_ONLY))).all()
        ]
        nome = [linha[0] for linha in (await session.execute(text(BUSCA_NOME))).all()]
        await session.rollback()

    print(f"docentes={tamanhos.docentes} recortes={tamanhos.recortes}")
    print(f"tamanho_docente={tamanhos.tamanho_docente}")
    print(f"tamanho_recorte={tamanhos.tamanho_recorte}")
    print(f"tempo_crud={_tempo(crud)}")
    print(f"tempo_insert_only={_tempo(historico)}")
    print(f"tempo_busca_nome={_tempo(nome)}")
    print("--- plano crud ---")
    print("\n".join(crud))


if __name__ == "__main__":
    asyncio.run(main())
