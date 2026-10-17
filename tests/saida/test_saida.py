"""Testes da consolidação e do validador. Rodar da raiz: python -m unittest discover -s tests -t ."""
from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from src import consolidar, validador

RAIZ = Path(__file__).resolve().parents[2]
D = Decimal


def base():
    return {
        "comissoes_por_lojista": [{"id_saida": "C1", "cnpj": "11111111000111", "lojista": "A", "linha_negocio": "CHECKOUT",
                                   "comissao_brl": "10.00"}],
        "divergencias_taxa": [],
        "notas_a_emitir": [{"id_saida": "N1", "tomador_cnpj": "11111111000111", "tomador": "A", "linha_negocio": "CHECKOUT",
                            "valor_brl": "10.00", "discriminacao": "x"}],
        "lancamentos_classificados": [], "pendencias": [],
        "rastro": [{"id_saida": "C1", "arquivo_origem": "a.csv", "ref_origem": "1", "valor": "4.00"},
                   {"id_saida": "C1", "arquivo_origem": "a.csv", "ref_origem": "2", "valor": "6.00"},
                   {"id_saida": "N1", "arquivo_origem": "a.csv", "ref_origem": "1", "valor": "10.00"}],
    }


class Validador(unittest.TestCase):
    def test_caso_consistente_passa_e_rastro_repete_id(self):
        self.assertEqual(validador.validar(base()), [])

    def test_rastro_que_nao_fecha_e_apontado(self):
        s = base()
        s["rastro"][0]["valor"] = "3.99"
        self.assertTrue(any("reportado=10.00 rastro=9.99" in e for e in validador.validar(s)))

    def test_decimal_sem_duas_casas_e_apontado(self):
        s = base()
        s["comissoes_por_lojista"][0]["comissao_brl"] = "10.0"
        self.assertTrue(any("2 casas" in e for e in validador.validar(s)))

    def test_nota_para_comissao_negativa_e_apontada(self):
        s = base()
        s["comissoes_por_lojista"][0]["comissao_brl"] = "-5.50"
        s["rastro"] = [{"id_saida": "C1", "arquivo_origem": "a", "ref_origem": "1", "valor": "-5.50"},
                       {"id_saida": "N1", "arquivo_origem": "a", "ref_origem": "1", "valor": "10.00"}]
        self.assertTrue(any("não positiva" in e for e in validador.validar(s)))

    def test_pendencia_sem_decisor_e_apontada(self):
        s = base()
        s["pendencias"] = [{"id_saida": "P1", "tipo": "T", "ref_origem": "x", "valor_brl": "1.00", "motivo": "m", "quem_decide": ""}]
        s["rastro"].append({"id_saida": "P1", "arquivo_origem": "a", "ref_origem": "x", "valor": "1.00"})
        self.assertTrue(any("quem_decide vazio" in e for e in validador.validar(s)))


class SobreSetembro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = consolidar.executar("2026-09", RAIZ / "data", RAIZ / "saida" / "checkouts", RAIZ / "saida" / "parcial",
                                    RAIZ / "config", RAIZ / "saida", gravar=False)

    def test_notas(self):
        notas = self.r["notas_a_emitir"]
        soma = lambda linha: sum((D(n["valor_brl"]) for n in notas if n["linha_negocio"] == linha), D("0"))
        self.assertEqual(sum(1 for n in notas if n["linha_negocio"] == "CHECKOUT"), 20)
        self.assertEqual(soma("CHECKOUT"), D("203740.84"))
        self.assertEqual(soma("REMESSA"), D("39543.45"))

    def test_toda_pendencia_tem_decisor(self):
        self.assertTrue(all(p["quem_decide"] for p in self.r["pendencias"]))

    def test_validador_aceita_o_resultado(self):
        self.assertEqual(validador.validar(self.r), [])


if __name__ == "__main__":
    unittest.main()
