"""Mede cardinalidade e repetição das alternativas de modelagem da fonte CAPES."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from src.config import settings
from src.pipeline.capes import baixar_csv, consolidar_registros, iterar_registros


def _tamanho_json(linhas: list[dict]) -> int:
    conteudo = "\n".join(
        json.dumps(linha, ensure_ascii=False, separators=(",", ":"))
        for linha in linhas
    )
    return len(conteudo.encode())


def medir(arquivo: Path) -> dict[str, int | float]:
    registros = list(iterar_registros(arquivo, settings.capes_sigla_instituicao))
    docentes, programas, vinculos = consolidar_registros(iter(registros))
    programas_por_docente = Counter(registro.id_pessoa for registro in vinculos)

    linhas_desnormalizadas = [
        {
            "id_pessoa": registro.id_pessoa,
            "nome": registro.nome_docente,
            "titulacao": registro.titulacao,
            "codigo_programa": registro.codigo_programa,
            "programa": registro.nome_programa,
            "area": registro.area_conhecimento,
            "ano": registro.ano_base,
        }
        for registro in vinculos
    ]
    linhas_normalizadas = [
        {"id_pessoa": registro.id_pessoa, "nome": registro.nome_docente, "titulacao": registro.titulacao}
        for registro in docentes.values()
    ]
    linhas_normalizadas.extend(
        {
            "codigo_programa": registro.codigo_programa,
            "programa": registro.nome_programa,
            "area": registro.area_conhecimento,
        }
        for registro in programas.values()
    )
    linhas_normalizadas.extend(
        {
            "id_pessoa": registro.id_pessoa,
            "codigo_programa": registro.codigo_programa,
            "ano": registro.ano_base,
        }
        for registro in vinculos
    )

    tamanho_desnormalizado = _tamanho_json(linhas_desnormalizadas)
    tamanho_normalizado = _tamanho_json(linhas_normalizadas)
    return {
        "docentes": len(docentes),
        "programas": len(programas),
        "vinculos": len(vinculos),
        "docentes_em_varios_programas": sum(quantidade > 1 for quantidade in programas_por_docente.values()),
        "maximo_programas_por_docente": max(programas_por_docente.values()),
        "vinculos_perdidos_em_1_para_n": len(vinculos) - len(docentes),
        "bytes_projecao_desnormalizada": tamanho_desnormalizado,
        "bytes_projecao_normalizada": tamanho_normalizado,
        "reducao_percentual": round(
            100 * (tamanho_desnormalizado - tamanho_normalizado) / tamanho_desnormalizado,
            1,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arquivo", type=Path, help="CSV local da CAPES")
    argumentos = parser.parse_args()

    if argumentos.arquivo:
        resultado = medir(argumentos.arquivo)
    else:
        with TemporaryDirectory(prefix="guia_capes_medicao_") as diretorio:
            arquivo = Path(diretorio) / "docentes_capes.csv"
            baixar_csv(settings.capes_docentes_url, arquivo)
            resultado = medir(arquivo)

    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
