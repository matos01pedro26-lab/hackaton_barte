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

    def test_totais_que_ja_batiam_nao_mudam(self):
        com = [c for c in self.r["comissoes_por_lojista"] if c["linha_negocio"] == "CHECKOUT"]
        self.assertEqual((len(com), sum((D(c["comissao_brl"]) for c in com), D("0"))), (21, D("203735.34")))
        div = [d for d in self.r["divergencias_taxa"] if d["linha_negocio"] == "CHECKOUT"]
        self.assertEqual((len(div), sum((D(d["diferenca_brl"]) for d in div), D("0"))), (92, D("1576.23")))
        self.assertEqual(len(self.r["lancamentos_classificados"]), 184)
        remessa = [n for n in self.r["notas_a_emitir"] if n["linha_negocio"] == "REMESSA"]
        self.assertEqual([n["tomador_cnpj"] for n in remessa], ["75374179000146"])

    def test_discriminacao_da_nota_e_so_servico_e_competencia(self):
        for n in self.r["notas_a_emitir"]:
            self.assertNotIn("RAZÃO SOCIAL", n["discriminacao"].upper())
            self.assertIn("competência 09/2026", n["discriminacao"])

    def test_razao_social_vira_pendencia_da_helena_com_o_valor_das_notas(self):
        p = self._pendencia("RAZAO_SOCIAL_NOTAS")
        self.assertEqual(p["quem_decide"], "Helena (financeiro)")
        self.assertEqual(D(p["valor_brl"]), D("203740.84"))
        self.assertEqual(len(p["ref_origem"].split("|")), 20)

    def test_quem_decide_sempre_com_pessoa_e_colunas_extras_preenchidas(self):
        for p in self.r["pendencias"]:
            self.assertNotIn(p["quem_decide"].strip().lower(), {"financeiro", "comercial", "tesouraria", ""})
            self.assertTrue(p["prazo"] and p["base_valor"], p["id_saida"])
            self.assertEqual(p["data_decisao"], "")                       # nenhuma decisão com data registrada

    def test_prazo_da_ponte_vem_do_email_e_atlas_fica_para_outubro(self):
        ponte = [p for p in self.r["pendencias"] if p["id_saida"].startswith("PEN-REM-")]
        self.assertTrue(ponte)
        self.assertEqual({p["prazo"] for p in ponte}, {"2026-10-09"})
        self.assertEqual(self._pendencia("EC_RETIDO")["prazo"], "fechamento de 2026-10")
        self.assertEqual(self._pendencia("EC_RETIDO")["base_valor"], "TAXA_ORBE")

    def test_referencias_nao_somam(self):
        for tipo, ref in (("CADASTRO_CONDICAO", D("15397.42")),):
            p = self._pendencia(tipo)
            self.assertEqual(D(p["valor_brl"]), D("0.00"), tipo)
            self.assertEqual(D(p["valor_referencia_brl"]), ref, tipo)
            self.assertTrue(p["motivo"].startswith("REFERÊNCIA, NÃO SOMAR"), tipo)

    def test_contestacao_a_ponte_positiva_e_rotulada(self):
        for p in self.r["pendencias"]:
            if p["tipo"] in ("CONTESTACAO_ATE_CONTRATO", "CONTESTACAO_PONTE", "DUPLICATA"):
                self.assertGreater(D(p["valor_brl"]), 0, p["id_saida"])
            if p["tipo"] in ("CONTESTACAO_ATE_CONTRATO", "CONTESTACAO_PONTE"):
                self.assertIn("A PEDIR À PONTE", p["motivo"])

    def test_lancamento_com_decisor_pendente_tem_confianca_ate_070(self):
        lc = {(l["banco"], l["ref_origem"]): l for l in self.r["lancamentos_classificados"]}
        for chave in (("AURORA", "L50"), ("AURORA", "L65"), ("MERIDIANO", "MRD2026090425"), ("AURORA", "L92")):
            self.assertLessEqual(D(lc[chave]["confianca"]), D("0.70"), chave)
        for ref in ("L57", "L86", "L87"):                                  # DARFs: retirada com fonte (linhas 5 e 17)
            self.assertNotIn("pendência", lc[("AURORA", ref)]["observacao"].lower())

    def _pendencia(self, tipo):
        return next(p for p in self.r["pendencias"] if p["tipo"] == tipo)


if __name__ == "__main__":
    unittest.main()
