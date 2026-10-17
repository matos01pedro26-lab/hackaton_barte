"""Fechamento de setembro/2026 de ponta a ponta: lê data/ e config/ reais e grava os CSVs do checkout.

Os valores esperados vêm de uma prévia independente (script à parte, fora de src/), feita antes deste módulo.
"""
import csv
import hashlib
import tempfile
import unittest
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from src.checkouts.__main__ import executar

RAIZ = Path(__file__).resolve().parents[2]


def ler(caminho):
    with open(caminho, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


class FechamentoSetembro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.saida = Path(cls.tmp.name) / "a"
        executar("2026-09", RAIZ / "data", RAIZ / "config", cls.saida)
        cls.comissoes = ler(cls.saida / "comissoes_por_lojista.csv")
        cls.rastro = ler(cls.saida / "rastro.csv")
        cls.pendencias = ler(cls.saida / "pendencias.csv")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_colunas_do_edital(self):
        self.assertEqual(list(self.comissoes[0]), ["id_saida", "cnpj", "lojista", "linha_negocio", "comissao_brl"])
        self.assertEqual(list(self.rastro[0]), ["id_saida", "arquivo_origem", "ref_origem", "valor"])
        self.assertEqual(list(self.pendencias[0]),
                         ["id_saida", "tipo", "ref_origem", "valor_brl", "motivo", "quem_decide"])
        for c in self.comissoes:
            self.assertRegex(c["cnpj"], r"^\d{14}$")
            self.assertRegex(c["comissao_brl"], r"^-?\d+\.\d{2}$")
            self.assertEqual(c["linha_negocio"], "CHECKOUT")

    def test_comissao_por_lojista(self):
        por_cnpj = {c["cnpj"]: Decimal(c["comissao_brl"]) for c in self.comissoes}
        self.assertEqual(len(por_cnpj), 21)
        self.assertEqual(sum(por_cnpj.values()), Decimal("207039.73"))
        self.assertEqual(por_cnpj["95927868000148"], Decimal("15621.27"))  # Rota Global, pela taxa contratada
        self.assertEqual(por_cnpj["22224579000109"], Decimal("11916.02"))  # Bridge, duas vigências numa linha
        self.assertEqual(por_cnpj["00520815000100"], Decimal("-5.50"))     # Casa do Estudante, R24

    def test_todo_numero_fecha_com_o_rastro(self):
        soma = defaultdict(Decimal)
        for r in self.rastro:
            soma[r["id_saida"]] += Decimal(r["valor"])
        for c in self.comissoes:
            self.assertEqual(soma[c["id_saida"]], Decimal(c["comissao_brl"]), c["id_saida"])
        for p in self.pendencias:
            self.assertEqual(soma[p["id_saida"]], Decimal(p["valor_brl"]), p["id_saida"])

    def test_nenhuma_linha_da_orbe_some(self):
        orbe = {r["id_transacao"] for r in ler(RAIZ / "data" / "fato_orbe.csv")}
        na_comissao = [r["ref_origem"] for r in self.rastro if r["id_saida"].startswith("CHK-")]
        retidas = [r["ref_origem"] for r in self.rastro if "-EC_" in r["id_saida"]]
        self.assertEqual(len(na_comissao), 1886)
        self.assertEqual(len(retidas), 57)  # Atlas
        self.assertEqual(sorted(na_comissao + retidas), sorted(orbe))

    def test_pendencias_do_mes(self):
        tipos = sorted((p["tipo"], p["ref_origem"], p["quem_decide"]) for p in self.pendencias)
        self.assertEqual(tipos, [
            ("CADASTRO_CONDICAO", "00520815000100/TODAS", "Financeiro"),
            ("CADASTRO_EC", "1038867654", "Financeiro"),
            ("CADASTRO_EC", "1043300981", "Financeiro"),
            ("CADASTRO_EC", "1043396662", "Financeiro"),
            ("COMISSAO_NAO_POSITIVA", "CHK-2026-09-00520815000100", "Financeiro"),
            ("EC_RETIDO", "1076801732", "Comercial"),
        ])

    def test_duas_execucoes_geram_os_mesmos_bytes(self):
        outra = Path(self.tmp.name) / "b"
        executar("2026-09", RAIZ / "data", RAIZ / "config", outra)
        for nome in ("comissoes_por_lojista.csv", "rastro.csv", "pendencias.csv"):
            a = hashlib.sha256((self.saida / nome).read_bytes()).hexdigest()
            b = hashlib.sha256((outra / nome).read_bytes()).hexdigest()
            self.assertEqual(a, b, nome)


if __name__ == "__main__":
    unittest.main()
