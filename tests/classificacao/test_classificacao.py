"""Testes da classificação dos extratos. Rodar da raiz: python -m unittest discover -s tests -t ."""
from __future__ import annotations

import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from src import classificacao as c

RAIZ = Path(__file__).resolve().parents[2]
D = Decimal


class SobreOsDadosDeSetembro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plano = c.ler_plano(RAIZ / "data" / "dim_plano_contas.csv")
        cls.res = c.executar("2026-09", RAIZ / "data", None)
        cls.por_ref = {(l["banco"], l["ref_origem"]): l for l in cls.res["linhas"]}

    def test_toda_conta_gravada_aceita_lancamento(self):
        """Falha se alguma conta sintética (ACEITA_LANCTO != S) aparecer na saída."""
        aceitas = c.contas_analiticas(self.plano)
        usadas = {l["conta_codigo"] for l in self.res["linhas"]}
        self.assertTrue(usadas)
        self.assertEqual(usadas - aceitas, set(), "conta sintética na classificação")

    def test_o_plano_tem_contas_sinteticas_para_o_teste_valer(self):
        self.assertTrue({"2.1.03", "4.2", "1.1.09"} <= set(self.plano) - c.contas_analiticas(self.plano))

    def test_mapeamento_de_referencia_conferido_nos_extratos(self):
        esperado = {
            ("AURORA", "L15"): "2.1.04.001", ("AURORA", "L42"): "2.1.03.003", ("AURORA", "L54"): "2.1.04.002",
            ("AURORA", "L55"): "2.1.04.003", ("AURORA", "L57"): "2.1.03.004", ("AURORA", "L86"): "2.1.03.001",
            ("AURORA", "L87"): "2.1.03.002", ("MERIDIANO", "MRD2026090132"): "1.1.03.002",
            ("AURORA", "L50"): "1.1.09.002", ("AURORA", "L65"): "2.1.01.001", ("AURORA", "L34"): "2.1.01.001",
            ("AURORA", "L60"): "2.1.01.001", ("MERIDIANO", "MRD2026090425"): "2.1.02.001",
            ("MERIDIANO", "MRD2026090680"): "3.2.01", ("MERIDIANO", "MRD2026090292"): "4.2.05",
            ("AURORA", "L16"): "4.2.02", ("AURORA", "L47"): "4.2.03", ("AURORA", "L48"): "4.2.04",
            ("AURORA", "L53"): "4.2.06", ("MERIDIANO", "MRD2026090586"): "4.3.01",
            ("AURORA", "L10"): "4.2.01", ("AURORA", "L90"): "4.2.01", ("MERIDIANO", "MRD2026090103"): "4.2.01",
            ("MERIDIANO", "MRD2026090696"): "4.2.01",
        }
        achado = {k: self.por_ref[k]["conta_codigo"] for k in esperado}
        self.assertEqual(achado, esperado)

    def test_grupos_inteiros(self):
        linhas = self.res["linhas"]
        contas = lambda banco, prefixo: {l["conta_codigo"] for l in linhas if l["banco"] == banco and l["descricao"].startswith(prefixo)}
        self.assertEqual(contas("AURORA", "TED RECEBIDA"), {"1.1.03.001"})                 # Orbe
        self.assertEqual(contas("AURORA", "TRANSF ENTRE CONTAS"), {"1.1.09.001"})
        self.assertEqual(contas("MERIDIANO", "TED RECEBIDA TARVO"), {"1.1.09.001"})
        self.assertEqual(contas("MERIDIANO", "TED ENVIADA"), {"2.1.02.001"})               # Ponte
        self.assertEqual(contas("MERIDIANO", "PIX RECEB"), {"2.1.02.001"})                 # lojistas e Ponte Aérea
        self.assertEqual(contas("MERIDIANO", "APLICACAO"), {"1.1.02.001"})                 # CDB
        self.assertEqual(contas("MERIDIANO", "RESGATE"), {"1.1.02.001"})

    def test_todo_lancamento_tem_regra_e_nada_vai_para_ia_ou_humano(self):
        self.assertEqual(len(self.res["linhas"]), 184)
        self.assertEqual({l["metodo"] for l in self.res["linhas"]}, {"REGRA"})
        self.assertEqual(self.res["sem_regra"], [])

    def test_confianca_entre_zero_e_um(self):
        self.assertTrue(all(D("0") <= l["confianca"] <= D("1") for l in self.res["linhas"]))

    def test_premissas_marcadas(self):
        premissas = {k for k, l in self.por_ref.items() if l["premissa"] == "S"}
        self.assertEqual(premissas, {("AURORA", "L48"), ("AURORA", "L65")})              # Google Workspace e devolução
        self.assertLess(self.por_ref[("AURORA", "L48")]["confianca"], D("0.90"))

    def test_ref_origem_aurora_e_linha_fisica_e_meridiano_e_fitid(self):
        for (banco, ref), l in self.por_ref.items():
            if banco == "AURORA":
                self.assertRegex(ref, r"^L\d+$")
            else:
                self.assertRegex(ref, r"^MRD\d+$")

    def test_soma_do_aurora_bate_com_o_saldo_do_extrato(self):
        aurora = next(s for s in self.res["saldos"] if s["banco"] == "AURORA")
        self.assertIs(aurora["bate"], True)
        self.assertEqual(aurora["saldo_inicial"] + aurora["soma"], aurora["saldo_final"])

    def test_meridiano_nao_tem_saldo_inicial_e_nao_finge_que_confere(self):
        meridiano = next(s for s in self.res["saldos"] if s["banco"] == "MERIDIANO")
        self.assertIsNone(meridiano["bate"])

    def test_um_rastro_por_lancamento_com_o_mesmo_valor(self):
        valores = {l["id_saida"]: l["valor"] for l in self.res["linhas"]}
        self.assertEqual({r["id_saida"]: r["valor"] for r in self.res["rastro"]}, valores)
        self.assertEqual(len(self.res["rastro"]), len(valores))


class ContasSinteticas(unittest.TestCase):
    PLANO = {"1.1.01.001": {"aceita_lancamento": "S", "tipo": "ANALITICA", "descricao": "Aurora"},
             "1.1.01.002": {"aceita_lancamento": "S", "tipo": "ANALITICA", "descricao": "Meridiano"},
             "2.1.03": {"aceita_lancamento": "N", "tipo": "SINTETICA", "descricao": "Obrigações fiscais"},
             "2.1.03.003": {"aceita_lancamento": "S", "tipo": "ANALITICA", "descricao": "ISS"}}

    def test_conta_sintetica_na_saida_levanta_erro(self):
        with self.assertRaises(ValueError):
            c.checar_contas(["2.1.03.003", "2.1.03"], self.PLANO)

    def test_conta_inexistente_levanta_erro(self):
        with self.assertRaises(ValueError):
            c.checar_contas(["9.9.99"], self.PLANO)

    def test_regra_apontando_para_conta_sintetica_para_a_classificacao(self):
        ruim = replace(c.REGRAS[0], conta="2.1.03")
        with self.assertRaises(ValueError):
            c.classificar([self._lancamento("PAGTO ISS")], self.PLANO, regras=(ruim,))

    @staticmethod
    def _lancamento(desc, banco="AURORA"):
        return {"competencia": "2026-09", "banco": banco, "ref_origem": "L1", "arquivo_origem": "x.csv", "data": "2026-09-01",
                "descricao": desc, "valor": "-10.00", "sentido": "SAIDA"}


class SemRegra(ContasSinteticas):
    REGRA_ISS = (c._r("T_ISS", "AURORA", r"^PAGTO ISS", "2.1.03.003", 0.9),)

    def test_sem_regra_vira_humano_sem_conta_e_com_confianca_zero(self):
        linhas, _, sem = c.classificar([self._lancamento("COISA NOVA")], self.PLANO, regras=self.REGRA_ISS)
        self.assertEqual((linhas[0]["metodo"], linhas[0]["conta_codigo"], linhas[0]["confianca"]), ("HUMANO", "", D("0.00")))
        self.assertEqual(len(sem), 1)

    def test_ia_so_vale_com_conta_analitica_e_confianca_limitada(self):
        linhas, _, sem = c.classificar([self._lancamento("COISA NOVA")], self.PLANO, regras=self.REGRA_ISS,
                                       sugestor=lambda l: ("2.1.03.003", 0.99))
        self.assertEqual((linhas[0]["metodo"], linhas[0]["conta_codigo"]), ("IA", "2.1.03.003"))
        self.assertLessEqual(linhas[0]["confianca"], D("0.60"))
        self.assertEqual(sem, [])

    def test_ia_sugerindo_conta_sintetica_e_ignorada(self):
        linhas, _, sem = c.classificar([self._lancamento("COISA NOVA")], self.PLANO, regras=self.REGRA_ISS,
                                       sugestor=lambda l: ("2.1.03", 0.9))
        self.assertEqual((linhas[0]["metodo"], linhas[0]["conta_codigo"]), ("HUMANO", ""))
        self.assertEqual(len(sem), 1)

    def test_decisor_pendente_limita_a_confianca_e_nao_muda_a_conta(self):
        livre, _, _ = c.classificar([self._lancamento("PAGTO ISS SAO PAULO")], self.PLANO, regras=self.REGRA_ISS)
        preso, _, _ = c.classificar([self._lancamento("PAGTO ISS SAO PAULO")], self.PLANO, regras=self.REGRA_ISS,
                                    decisor_pendente={("AURORA", "L1")})
        self.assertEqual(livre[0]["confianca"], D("0.90"))
        self.assertEqual((preso[0]["conta_codigo"], preso[0]["confianca"]), ("2.1.03.003", D("0.70")))
        self.assertIn("Decisor pendente", preso[0]["observacao"])

    def test_regra_vence_a_ia(self):
        linhas, _, _ = c.classificar([self._lancamento("PAGTO ISS SAO PAULO")], self.PLANO, regras=self.REGRA_ISS,
                                     sugestor=lambda l: ("1.1.01.001", 0.9))
        self.assertEqual((linhas[0]["metodo"], linhas[0]["conta_codigo"]), ("REGRA", "2.1.03.003"))


if __name__ == "__main__":
    unittest.main()
