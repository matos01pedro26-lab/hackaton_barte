"""Divergência de taxa do checkout (R5): taxa aplicada pela Orbe contra a contratada, transação por transação."""
import unittest
from decimal import Decimal

from src.checkouts.comissao import calcular
from tests.checkouts.exemplos import CNPJ_A, CNPJ_B, condicao, contrato, entrada, transacao


def diferencas(resultado):
    return {d["ref_origem"]: d["diferenca_brl"] for d in resultado.divergencias}

COLUNAS = ["id_saida", "cnpj", "linha_negocio", "ref_origem", "taxa_contratada_pct", "taxa_aplicada_pct",
           "diferenca_brl"]


def soma_rastro(resultado, id_saida):
    return sum((r["valor"] for r in resultado.rastro if r["id_saida"] == id_saida), Decimal("0"))


class DivergenciaDeTaxa(unittest.TestCase):
    def test_taxa_aplicada_acima_da_contratada_gera_divergencia_com_rastro(self):
        # Rota Global (R9): contrato 2,49% no crédito à vista, Orbe cobrou 2,99%
        r = calcular(entrada([transacao("TX1", bruto="1000.00", aplicada="2.99"),
                              transacao("TX2", bruto="500.00", aplicada="2.49")],
                             contratos=[contrato(taxa_credito_vista_pct="2.49")]))

        self.assertEqual(r.divergencias, [{
            "id_saida": "TX1", "cnpj": CNPJ_A, "linha_negocio": "CHECKOUT", "ref_origem": "TX1",
            "taxa_contratada_pct": Decimal("2.49"), "taxa_aplicada_pct": Decimal("2.99"),
            "diferenca_brl": Decimal("5.00"),
        }])
        self.assertEqual(list(r.divergencias[0]), COLUNAS)
        self.assertEqual(soma_rastro(r, "TX1"), Decimal("5.00"))

    def test_bridge_compara_com_a_taxa_vigente_e_estorno_inverte_o_sinal(self):
        # 2,59% até 14/09, 2,19% a partir de 15/09; estorno usa a taxa da data da venda original (R2)
        contratos = [contrato(fim="2026-09-14", linha="6", taxa_credito_vista_pct="2.59"),
                     contrato(ini="2026-09-15", linha="7", taxa_credito_vista_pct="2.19")]
        r = calcular(entrada([
            transacao("TX1", bruto="1000.00", data="2026-09-14", aplicada="2.59"),
            transacao("TX2", bruto="1000.00", data="2026-09-15", aplicada="2.59"),
            transacao("TX3", bruto="-500.00", tipo="ESTORNO", data="2026-09-20", data_venda_original="2026-09-15",
                      aplicada="2.59"),
            transacao("TX4", bruto="-100.00", tipo="ESTORNO", data="2026-09-20", data_venda_original="2026-09-10",
                      aplicada="2.59"),
        ], contratos=contratos))

        self.assertEqual(diferencas(r), {"TX2": Decimal("4.00"), "TX3": Decimal("-2.00")})
        self.assertEqual(r.divergencias[0]["taxa_contratada_pct"], Decimal("2.19"))

    def test_condicao_especial_faz_toda_a_taxa_cobrada_virar_divergencia(self):
        # Casa (R8): contratada 0% de set a dez; o estorno de venda de agosto segue a planilha e não diverge
        r = calcular(entrada([
            transacao("TX1", bruto="1000.00", aplicada="2.69"),
            transacao("TX2", faixa="debito", tipo="ESTORNO", bruto="-369.39", data="2026-09-07",
                      data_venda_original="2026-08-21", aplicada="1.49"),
        ], condicoes=[condicao()]))

        self.assertEqual(diferencas(r), {"TX1": Decimal("26.90")})
        self.assertEqual(r.divergencias[0]["taxa_contratada_pct"], Decimal("0"))

    def test_sem_taxa_contratada_nao_ha_divergencia(self):
        # Atlas (R7) e transação sem contrato vigente já são pendências; não se inventa taxa para comparar
        r = calcular(entrada([transacao("TX1", ec="1076801732", status_ec="RETIDO", aplicada="3.49"),
                              transacao("TX2", cnpj="33333333000133", aplicada="9.99")]))

        self.assertEqual(r.divergencias, [])

    def test_arredonda_cada_linha_meio_centavo_para_longe_do_zero(self):
        # 1,00 × 0,50 p.p. = 0,005 -> 0,01 ; estorno -1,00 -> -0,01 (R4)
        r = calcular(entrada([
            transacao("TX1", bruto="1.00", aplicada="3.19"),
            transacao("TX2", bruto="-1.00", tipo="ESTORNO", data_venda_original="2026-09-01", aplicada="3.19"),
        ]))

        self.assertEqual(diferencas(r), {"TX1": Decimal("0.01"), "TX2": Decimal("-0.01")})

    def test_divergencia_vira_uma_pendencia_de_devolucao_por_lojista(self):
        # Divergência é devolução: a Tarvo devolve ao lojista o que a Orbe cobrou a mais (Helena)
        r = calcular(entrada([
            transacao("TX1", bruto="1000.00", aplicada="3.19"),
            transacao("TX2", bruto="-200.00", tipo="ESTORNO", data_venda_original="2026-09-01", aplicada="3.19"),
            transacao("TX3", bruto="700.00"),
            transacao("TX4", cnpj=CNPJ_B, bruto="100.00"),
        ], contratos=[contrato(), contrato(CNPJ_B, linha="12")]))

        dev = [p for p in r.pendencias if p["tipo"] == "DEVOLUCAO_DIVERGENCIA"]
        self.assertEqual(len(dev), 1)  # B não tem divergência
        p = dev[0]
        self.assertEqual(p["ref_origem"], CNPJ_A)
        self.assertEqual(p["valor_brl"], Decimal("4.00"))  # 5,00 da venda − 1,00 do estorno
        self.assertEqual(p["quem_decide"], "Financeiro")
        self.assertIn("Loja A Ltda", p["motivo"])
        self.assertEqual(soma_rastro(r, p["id_saida"]), p["valor_brl"])
        self.assertEqual({x["ref_origem"] for x in r.rastro if x["id_saida"] == p["id_saida"]}, {"TX1", "TX2"})


if __name__ == "__main__":
    unittest.main()
