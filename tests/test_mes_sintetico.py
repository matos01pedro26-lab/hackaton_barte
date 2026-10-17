"""O fechamento roda num mês novo, sem mexer no código: outubro sintético a partir do set de setembro.
Rodar da raiz: python -m unittest discover -s tests -t .

Esperado (ver a conta em tests/mes_sintetico.py):
  * valores iguais aos de setembro, exceto a Casa do Estudante: o estorno de 21/08 vira 21/09, dentro da isenção,
    então a comissão dela sai de -R$ 5,50 para 0,00 e o checkout sobe R$ 5,50 (203.735,34 -> 203.740,84);
  * divergências, lançamentos e remessa iguais;
  * as pendências de banco escritas à mão são de setembro (config/pendencias_bancos.csv, coluna mes): não valem em outubro.
"""
from __future__ import annotations

import csv
import tempfile
import unittest
from decimal import Decimal as D
from pathlib import Path

from src import fechar
from tests.mes_sintetico import gerar

RAIZ = Path(__file__).resolve().parents[1]
INPUT, CONFIG = RAIZ / "input", RAIZ / "config"


def _ler(caminho: Path) -> list[dict]:
    with open(caminho, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=";"))


@unittest.skipUnless((INPUT / "01_orbe_relatorio_comissoes_set2026.csv").exists(), "sem input/ de setembro")
class MesSinteticoOutubro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp.name)
        cls.entrada = gerar(tmp / "input")
        cls.saida = tmp / "saida"
        cls.res = fechar.fechar("2026-10", cls.entrada, tmp / "data", cls.saida, CONFIG, arquivar=False)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_validador_fecha(self):
        self.assertTrue(self.res["validador"]["ok"], self.res["validador"]["texto"])

    def test_checkout_sobe_so_o_estorno_da_casa(self):
        com = [c for c in _ler(self.saida / "comissoes_por_lojista.csv") if c["linha_negocio"] == "CHECKOUT"]
        self.assertEqual(len(com), 21)
        self.assertEqual(sum(D(c["comissao_brl"]) for c in com), D("203740.84"))
        casa = next(c for c in com if c["cnpj"] == "00520815000100")
        self.assertEqual(D(casa["comissao_brl"]), D("0.00"))

    def test_remessa_igual_a_setembro(self):
        rem = [c for c in _ler(self.saida / "comissoes_por_lojista.csv") if c["linha_negocio"] == "REMESSA"]
        self.assertEqual(sum(D(c["comissao_brl"]) for c in rem), D("39543.45"))

    def test_divergencias_e_lancamentos_iguais_a_setembro(self):
        chk = [d for d in _ler(self.saida / "divergencias_taxa.csv") if d["linha_negocio"] == "CHECKOUT"]
        self.assertEqual((len(chk), sum(D(d["diferenca_brl"]) for d in chk)), (92, D("1576.23")))
        self.assertEqual(len(_ler(self.saida / "divergencias_taxa.csv")), 119)
        self.assertEqual(len(_ler(self.saida / "lancamentos_classificados.csv")), 184)

    def test_pendencias_de_banco_de_setembro_nao_valem_em_outubro(self):
        tipos = {p["tipo"] for p in _ler(self.saida / "pendencias.csv")}
        for tipo in ("PIX_SEM_IDENTIFICACAO", "DEVOLUCAO_PIX", "PIX_SEM_OPERACAO", "TRANSFERENCIA_EM_TRANSITO",
                     "CONTA_GARANTIDA_SEM_ENCARGOS"):
            self.assertNotIn(tipo, tipos)
        self.assertEqual(len(_ler(self.saida / "pendencias.csv")), 20)

    def test_arquivos_de_outubro_foram_lidos_pelo_nome(self):
        # o guarda de refaturamento não pode barrar: os IDs de outubro são novos
        self.assertFalse(self.res.get("ja_faturadas"), self.res.get("ja_faturadas"))


if __name__ == "__main__":
    unittest.main()
