import csv
import tempfile
import unittest
from pathlib import Path

from src.pipeline.capes import consolidar_registros, iterar_registros


CAMPOS = [
    "AN_BASE",
    "SG_ENTIDADE_ENSINO",
    "ID_PESSOA",
    "NM_DOCENTE",
    "NM_GRAU_TITULACAO",
    "AN_TITULACAO",
    "NM_AREA_BASICA_TITULACAO",
    "DS_TIPO_VINCULO_DOCENTE_IES",
    "DS_REGIME_TRABALHO",
    "DS_CATEGORIA_DOCENTE",
    "CD_PROGRAMA_IES",
    "NM_PROGRAMA_IES",
    "NM_GRAU_PROGRAMA",
    "NM_MODALIDADE_PROGRAMA",
    "CD_CONCEITO_PROGRAMA",
    "NM_AREA_AVALIACAO",
    "NM_GRANDE_AREA_CONHECIMENTO",
    "NM_AREA_CONHECIMENTO",
    "NM_MUNICIPIO_PROGRAMA_IES",
    "SG_UF_PROGRAMA",
]


class TestFonteCapes(unittest.TestCase):
    def setUp(self):
        self.diretorio = tempfile.TemporaryDirectory()
        self.arquivo = Path(self.diretorio.name) / "docentes.csv"
        base = {
            "AN_BASE": "2024",
            "SG_ENTIDADE_ENSINO": "UNB",
            "ID_PESSOA": "101",
            "NM_DOCENTE": "ÁLVARO TESTE",
            "NM_GRAU_TITULACAO": "DOUTORADO",
            "AN_TITULACAO": "2020",
            "NM_AREA_BASICA_TITULACAO": "CIÊNCIA DA COMPUTAÇÃO",
            "DS_TIPO_VINCULO_DOCENTE_IES": "SERVIDOR PÚBLICO",
            "DS_REGIME_TRABALHO": "DEDICAÇÃO EXCLUSIVA",
            "DS_CATEGORIA_DOCENTE": "PERMANENTE",
            "CD_PROGRAMA_IES": "53001010001P0",
            "NM_PROGRAMA_IES": "COMPUTAÇÃO",
            "NM_GRAU_PROGRAMA": "MESTRADO",
            "NM_MODALIDADE_PROGRAMA": "ACADÊMICO",
            "CD_CONCEITO_PROGRAMA": "5",
            "NM_AREA_AVALIACAO": "CIÊNCIA DA COMPUTAÇÃO",
            "NM_GRANDE_AREA_CONHECIMENTO": "CIÊNCIAS EXATAS E DA TERRA",
            "NM_AREA_CONHECIMENTO": "CIÊNCIA DA COMPUTAÇÃO",
            "NM_MUNICIPIO_PROGRAMA_IES": "BRASÍLIA",
            "SG_UF_PROGRAMA": "DF",
        }
        outro_programa = {
            **base,
            "CD_PROGRAMA_IES": "53001010002P0",
            "NM_PROGRAMA_IES": "ENGENHARIA DE SOFTWARE",
        }
        outra_instituicao = {
            **base,
            "SG_ENTIDADE_ENSINO": "OUTRA",
            "ID_PESSOA": "202",
        }
        with self.arquivo.open("w", encoding="latin-1", newline="") as destino:
            escritor = csv.DictWriter(destino, fieldnames=CAMPOS, delimiter=";")
            escritor.writeheader()
            escritor.writerows([base, outro_programa, outra_instituicao])

    def tearDown(self):
        self.diretorio.cleanup()

    def test_filtra_unb_e_preserva_acentos(self):
        registros = list(iterar_registros(self.arquivo))

        self.assertEqual(len(registros), 2)
        self.assertEqual(registros[0].nome_docente, "ÁLVARO TESTE")
        self.assertEqual(registros[0].ano_titulacao, 2020)
        self.assertEqual(registros[0].uf_programa, "DF")

    def test_consolida_relacao_muitos_para_muitos(self):
        docentes, programas, vinculos = consolidar_registros(
            iterar_registros(self.arquivo)
        )

        self.assertEqual(len(docentes), 1)
        self.assertEqual(len(programas), 2)
        self.assertEqual(len(vinculos), 2)


if __name__ == "__main__":
    unittest.main()
