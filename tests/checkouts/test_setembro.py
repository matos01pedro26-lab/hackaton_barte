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
        cls.divergencias = ler(cls.saida / "divergencias_taxa.csv")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_colunas_do_edital(self):
        self.assertEqual(list(self.comissoes[0]), ["id_saida", "cnpj", "lojista", "linha_negocio", "comissao_brl"])
        self.assertEqual(list(self.rastro[0]), ["id_saida", "arquivo_origem", "ref_origem", "valor"])
        self.assertEqual(list(self.pendencias[0]),
                         ["id_saida", "tipo", "ref_origem", "valor_brl", "motivo", "quem_decide"])
        self.assertEqual(list(self.divergencias[0]), ["id_saida", "cnpj", "linha_negocio", "ref_origem",
                                                      "taxa_contratada_pct", "taxa_aplicada_pct", "diferenca_brl"])
        for d in self.divergencias:
            self.assertRegex(d["cnpj"], r"^\d{14}$")
            self.assertRegex(d["diferenca_brl"], r"^-?\d+\.\d{2}$")
            self.assertEqual(d["linha_negocio"], "CHECKOUT")
        for c in self.comissoes:
            self.assertRegex(c["cnpj"], r"^\d{14}$")
            self.assertRegex(c["comissao_brl"], r"^-?\d+\.\d{2}$")
            self.assertEqual(c["linha_negocio"], "CHECKOUT")

    def test_comissao_por_lojista(self):
        por_cnpj = {c["cnpj"]: Decimal(c["comissao_brl"]) for c in self.comissoes}
        self.assertEqual(len(por_cnpj), 21)
        # Com os ajustes tardios (P13): R$ 203.740,84 dos 20 com nota (HIPOTESES, seção 8) + Casa −5,50
        self.assertEqual(sum(por_cnpj.values()), Decimal("203735.34"))
        self.assertEqual(por_cnpj["95927868000148"], Decimal("15621.27"))  # Rota Global, pela taxa contratada
        self.assertEqual(por_cnpj["22224579000109"], Decimal("11769.74"))  # Bridge: duas vigências e 2 estornos tardios
        self.assertEqual(por_cnpj["00520815000100"], Decimal("-5.50"))     # Casa do Estudante, R8

    def test_divergencias_de_taxa(self):
        # Alvo: HIPOTESES seção 8 (notebook do Pedro), cálculo independente deste módulo. A Casa não entra (R28).
        por_cnpj = defaultdict(lambda: [0, Decimal("0")])
        for d in self.divergencias:
            por_cnpj[d["cnpj"]][0] += 1
            por_cnpj[d["cnpj"]][1] += Decimal(d["diferenca_brl"])
        self.assertEqual(len(self.divergencias), 92)
        self.assertEqual(sum(v for _, v in por_cnpj.values()), Decimal("1576.23"))
        self.assertEqual(dict(por_cnpj), {
            "95927868000148": [87, Decimal("1546.28")],    # Rota Global: +0,50 p.p. desde 12/09 (R9)
            "22224579000109": [5, Decimal("29.95")],       # Bridge: 2,59% depois de 15/09
        })
        self.assertTrue(all(d["id_saida"] == f"DIV-CHK-2026-09-{d['ref_origem']}" for d in self.divergencias))

    def test_todo_numero_fecha_com_o_rastro(self):
        soma = defaultdict(Decimal)
        for r in self.rastro:
            soma[r["id_saida"]] += Decimal(r["valor"])
        for c in self.comissoes:
            self.assertEqual(soma[c["id_saida"]], Decimal(c["comissao_brl"]), c["id_saida"])
        for p in self.pendencias:
            self.assertEqual(soma[p["id_saida"]], Decimal(p["valor_brl"]), p["id_saida"])
        for d in self.divergencias:
            self.assertEqual(soma[d["id_saida"]], Decimal(d["diferenca_brl"]), d["id_saida"])

    def test_nenhuma_linha_da_orbe_some(self):
        orbe = {r["id_transacao"] for r in ler(RAIZ / "data" / "fato_orbe.csv")}
        na_comissao = [r["ref_origem"] for r in self.rastro if r["id_saida"].startswith("CHK-")]
        retidas = [r["ref_origem"] for r in self.rastro if "-EC_" in r["id_saida"]]
        self.assertEqual(len(na_comissao), 1900)  # 1.957 linhas com os ajustes tardios, menos as da Atlas
        self.assertEqual(len(retidas), 57)  # Atlas
        self.assertEqual(sorted(na_comissao + retidas), sorted(orbe))

    def test_pendencias_do_mes(self):
        p = {x["id_saida"].replace("PEN-CHK-2026-09-", ""): (Decimal(x["valor_brl"]), x["quem_decide"])
             for x in self.pendencias}
        self.assertEqual(p, {
            "CADASTRO_CONDICAO-00520815000100-TODAS": (Decimal("15397.42"), "Comercial"),  # o que a planilha cobraria
            "CADASTRO_EC-1038867654": (Decimal("10886.22"), "Comercial"),  # Kiwi, com a venda tardia
            "CADASTRO_EC-1043300981": (Decimal("7767.78"), "Comercial"),
            "CADASTRO_EC-1043396662": (Decimal("9014.42"), "Comercial"),
            "COMISSAO_NAO_POSITIVA-00520815000100": (Decimal("-5.50"), "Financeiro"),
            "CONTESTACAO_ORBE-22224579000109": (Decimal("29.95"), "Financeiro"),             # Bridge (R29)
            "CONTESTACAO_ORBE-95927868000148": (Decimal("1546.28"), "Financeiro"),           # Rota Global (R9, R29)
            "DEVOLUCAO_CONDICAO-00520815000100-TODAS": (Decimal("15396.77"), "Financeiro"),  # Casa (R28)
            "EC_RETIDO-1076801732": (Decimal("262138.61"), "Comercial (Diego)"),                     # Atlas (R7)
            # Fluente (P15): 0,79% na planilha; a resposta "condição negociada" não está no CSV, então segue pendente
            "TAXA_A_CONFIRMAR-03229837000103-pix": (Decimal("9.16"), "Helena (financeiro)"),
        })
        for x in self.pendencias:  # ref_origem = transações da Orbe separadas por "|", como na remessa
            self.assertTrue(all(ref.startswith(("TX", "AN")) for ref in x["ref_origem"].split("|")), x["id_saida"])

    def test_duas_execucoes_geram_os_mesmos_bytes(self):
        outra = Path(self.tmp.name) / "b"
        executar("2026-09", RAIZ / "data", RAIZ / "config", outra)
        for nome in ("comissoes_por_lojista.csv", "rastro.csv", "pendencias.csv", "divergencias_taxa.csv"):
            a = hashlib.sha256((self.saida / nome).read_bytes()).hexdigest()
            b = hashlib.sha256((outra / nome).read_bytes()).hexdigest()
            self.assertEqual(a, b, nome)


if __name__ == "__main__":
    unittest.main()
