"""Comissão de checkout por lojista: comportamento de src.checkouts.comissao.calcular."""
import unittest
from decimal import Decimal

from src.checkouts.comissao import calcular
from tests.checkouts.exemplos import CNPJ_A, CNPJ_B, condicao, contrato, ec, entrada, mapeamento, transacao


def soma_rastro(resultado, id_saida):
    return sum((r["valor"] for r in resultado.rastro if r["id_saida"] == id_saida), Decimal("0"))


class ComissaoPorLojista(unittest.TestCase):
    def test_venda_gera_comissao_pela_taxa_contratada(self):
        r = calcular(entrada([transacao("TX1", bruto="1000.00")]))

        self.assertEqual(len(r.comissoes), 1)
        c = r.comissoes[0]
        self.assertEqual(c["id_saida"], f"CHK-2026-09-{CNPJ_A}")
        self.assertEqual(c["cnpj"], CNPJ_A)
        self.assertEqual(c["lojista"], "Loja A Ltda")
        self.assertEqual(c["linha_negocio"], "CHECKOUT")
        self.assertEqual(c["comissao_brl"], Decimal("26.90"))
        self.assertEqual(soma_rastro(r, c["id_saida"]), c["comissao_brl"])
        self.assertEqual(r.rastro[0]["ref_origem"], "TX1")
        self.assertEqual(r.rastro[0]["arquivo_origem"], "01_orbe_relatorio_comissoes_set2026.csv")

    def test_vigencia_escolhe_o_contrato_da_data_do_movimento(self):
        # Bridge: crédito à vista 2,59% até 14/09 e 2,19% a partir de 15/09, mesmo CNPJ
        contratos = [contrato(fim="2026-09-14", linha="6", taxa_credito_vista_pct="2.59"),
                     contrato(ini="2026-09-15", linha="7", taxa_credito_vista_pct="2.19")]
        r = calcular(entrada([transacao("TX1", bruto="1000.00", data="2026-09-14"),
                              transacao("TX2", bruto="1000.00", data="2026-09-15")], contratos=contratos))

        por_ref = {x["ref_origem"]: x["valor"] for x in r.rastro if x["id_saida"].startswith("CHK-")}
        self.assertEqual(por_ref, {"TX1": Decimal("25.90"), "TX2": Decimal("21.90")})
        self.assertEqual(len(r.comissoes), 1)
        self.assertEqual(r.comissoes[0]["comissao_brl"], Decimal("47.80"))

    def test_estorno_de_venda_de_agosto_abate_pela_taxa_da_data_da_venda(self):
        contratos = [contrato(fim="2026-08-31", linha="5", taxa_debito_pct="1.99"),
                     contrato(ini="2026-09-01", linha="6", taxa_debito_pct="1.49")]
        r = calcular(entrada([transacao("TX1", faixa="debito", bruto="1000.00", data="2026-09-03"),
                              transacao("TX2", faixa="debito", tipo="ESTORNO", bruto="-100.00", data="2026-09-05",
                                        data_venda_original="2026-08-20")], contratos=contratos))

        por_ref = {x["ref_origem"]: x["valor"] for x in r.rastro if x["id_saida"].startswith("CHK-")}
        self.assertEqual(por_ref, {"TX1": Decimal("14.90"), "TX2": Decimal("-1.99")})
        self.assertEqual(r.comissoes[0]["comissao_brl"], Decimal("12.91"))

    def test_arredonda_meio_centavo_para_longe_do_zero_linha_a_linha(self):
        # 0,50 × 1% = 0,005 -> 0,01 ; -0,50 × 1% = -0,005 -> -0,01 (R8). Somar antes daria 0,00 em ambos os casos.
        contratos = [contrato(taxa_pix_pct="1.00")]
        r = calcular(entrada([transacao("TX1", faixa="pix", bruto="0.50"), transacao("TX2", faixa="pix", bruto="0.50"),
                              transacao("TX3", faixa="pix", tipo="ESTORNO", bruto="-0.50",
                                        data_venda_original="2026-09-01")], contratos=contratos))

        por_ref = {x["ref_origem"]: x["valor"] for x in r.rastro if x["id_saida"].startswith("CHK-")}
        self.assertEqual(por_ref, {"TX1": Decimal("0.01"), "TX2": Decimal("0.01"), "TX3": Decimal("-0.01")})
        self.assertEqual(r.comissoes[0]["comissao_brl"], Decimal("0.01"))

    def test_condicao_especial_zera_a_taxa_so_dentro_da_vigencia(self):
        # Casa do Estudante (R24): tarifa zerada de set a dez; estorno de venda de agosto usa a planilha
        r = calcular(entrada([
            transacao("TX1", bruto="1000.00", data="2026-09-10"),
            transacao("AN1", faixa="antecipacao", tipo="ANTECIPACAO", bruto="5000.00", data="2026-09-11"),
            transacao("TX2", faixa="debito", tipo="ESTORNO", bruto="-369.39", data="2026-09-07",
                      data_venda_original="2026-08-21"),
        ], condicoes=[condicao()]))

        por_ref = {x["ref_origem"]: x["valor"] for x in r.rastro if x["id_saida"].startswith("CHK-")}
        self.assertEqual(por_ref, {"TX1": Decimal("0.00"), "AN1": Decimal("0.00"), "TX2": Decimal("-5.50")})
        self.assertEqual(r.comissoes[0]["comissao_brl"], Decimal("-5.50"))

    def test_ec_retido_fica_fora_da_comissao_e_vira_pendencia_do_comercial(self):
        # Atlas (R3): sem contrato assinado, não fatura até o comercial confirmar
        ecs = [ec(), ec("1076801732", cnpj="", status="RETIDO", fonte="config/mapeamento_ec.csv",
                      observacao="nao faturar a Atlas ate confirmacao do comercial")]
        r = calcular(entrada([transacao("TX1", bruto="1000.00"),
                              transacao("TX2", ec="1076801732", status_ec="RETIDO", bruto="300.00"),
                              transacao("TX3", ec="1076801732", status_ec="RETIDO", bruto="200.00")], ecs=ecs))

        self.assertEqual([c["cnpj"] for c in r.comissoes], [CNPJ_A])
        self.assertEqual(len(r.pendencias), 1)
        p = r.pendencias[0]
        self.assertEqual(p["tipo"], "EC_RETIDO")
        self.assertEqual(p["ref_origem"], "1076801732")
        self.assertEqual(p["valor_brl"], Decimal("500.00"))
        self.assertEqual(p["quem_decide"], "Comercial")
        self.assertIn("nao faturar a Atlas", p["motivo"])
        self.assertEqual(soma_rastro(r, p["id_saida"]), p["valor_brl"])
        self.assertEqual({x["ref_origem"] for x in r.rastro if x["id_saida"] == p["id_saida"]}, {"TX2", "TX3"})

    def test_sem_taxa_contratada_unica_vira_pendencia_e_nao_chuta(self):
        contratos = [contrato(), contrato(ini="2026-09-01", linha="11"),  # dois vigentes para A em setembro
                     contrato(CNPJ_B, linha="12", taxa_pix_pct="")]       # B sem taxa de Pix
        r = calcular(entrada([transacao("TX1", bruto="100.00"),
                              transacao("TX2", cnpj=CNPJ_B, faixa="pix", bruto="50.00"),
                              transacao("TX3", cnpj=CNPJ_B, faixa="debito", bruto="1000.00"),
                              transacao("TX4", cnpj="33333333000133", bruto="10.00")], contratos=contratos))

        self.assertEqual([(c["cnpj"], c["comissao_brl"]) for c in r.comissoes], [(CNPJ_B, Decimal("14.90"))])
        pend = {p["ref_origem"]: p for p in r.pendencias}
        self.assertEqual(set(pend), {"TX1", "TX2", "TX4"})
        self.assertTrue(all(p["tipo"] == "SEM_TAXA_CONTRATADA" and p["quem_decide"] == "Financeiro"
                            for p in pend.values()))
        self.assertIn("2 contratos vigentes", pend["TX1"]["motivo"])
        self.assertEqual(pend["TX2"]["valor_brl"], Decimal("50.00"))
        self.assertEqual(soma_rastro(r, pend["TX4"]["id_saida"]), Decimal("10.00"))

    def test_comissao_negativa_fica_no_arquivo_e_vira_pendencia_do_financeiro(self):
        r = calcular(entrada([transacao("TX1", bruto="1000.00", data="2026-09-10"),
                              transacao("TX2", faixa="debito", tipo="ESTORNO", bruto="-369.39", data="2026-09-07",
                                        data_venda_original="2026-08-21")], condicoes=[condicao(pendencia="")]))

        self.assertEqual(r.comissoes[0]["comissao_brl"], Decimal("-5.50"))
        nao_positivas = [p for p in r.pendencias if p["tipo"] == "COMISSAO_NAO_POSITIVA"]
        self.assertEqual(len(nao_positivas), 1)
        p = nao_positivas[0]
        self.assertEqual(p["ref_origem"], f"CHK-2026-09-{CNPJ_A}")
        self.assertEqual(p["valor_brl"], Decimal("-5.50"))
        self.assertEqual(p["quem_decide"], "Financeiro")
        self.assertEqual(soma_rastro(r, p["id_saida"]), p["valor_brl"])

    def test_decisao_que_falta_na_planilha_vira_pendencia_de_cadastro_com_o_valor_em_jogo(self):
        # EC mapeado só por config (R19) e condição especial fora da planilha (R24): dado do financeiro
        ecs = [ec(), ec("1000000009", cnpj=CNPJ_B, fonte="config/mapeamento_ec.csv")]
        r = calcular(entrada(
            [transacao("TX1", bruto="1000.00"), transacao("TX2", cnpj=CNPJ_B, ec="1000000009", bruto="1000.00"),
             transacao("TX3", cnpj=CNPJ_B, ec="1000000009", faixa="pix", bruto="100.00")],
            contratos=[contrato(), contrato(CNPJ_B, linha="28")], ecs=ecs,
            mapeamento=[mapeamento("1000000009", CNPJ_B), mapeamento("1076801732", "", "RETIDO", pendencia="")],
            condicoes=[condicao(pendencia="Registrar a taxa zerada na planilha")]))

        cad = {p["tipo"]: p for p in r.pendencias if p["tipo"].startswith("CADASTRO")}
        self.assertEqual(set(cad), {"CADASTRO_EC", "CADASTRO_CONDICAO"})
        self.assertEqual(cad["CADASTRO_EC"]["ref_origem"], "1000000009")
        self.assertEqual(cad["CADASTRO_EC"]["valor_brl"], Decimal("27.79"))      # comissão que depende do mapeamento
        self.assertEqual(cad["CADASTRO_CONDICAO"]["ref_origem"], f"{CNPJ_A}/TODAS")
        self.assertEqual(cad["CADASTRO_CONDICAO"]["valor_brl"], Decimal("26.90"))  # o que a planilha cobraria
        self.assertIn("Registrar a taxa zerada", cad["CADASTRO_CONDICAO"]["motivo"])
        for p in cad.values():
            self.assertEqual(p["quem_decide"], "Financeiro")
            self.assertEqual(soma_rastro(r, p["id_saida"]), p["valor_brl"])

    def test_condicao_ja_aplicada_pela_ingestao_mantem_o_valor_que_a_planilha_cobraria(self):
        # src.ingestao grava a condição como linha CONFIG em dim_contrato_taxa e encerra a linha da planilha na véspera
        contratos = [contrato(fim="2026-08-31", origem_condicao="TABELA"),
                     contrato(ini="2026-09-01", fim="2026-12-31", origem_condicao="CONFIG", taxa_debito_pct="0",
                              taxa_credito_vista_pct="0", taxa_credito_2_6x_pct="0", taxa_credito_7_12x_pct="0",
                              taxa_pix_pct="0", taxa_antecipacao_pct="0"),
                     contrato(ini="2027-01-01", origem_condicao="TABELA (retomada)")]
        r = calcular(entrada([transacao("TX1", bruto="1000.00")], contratos=contratos, condicoes=[condicao()]))

        self.assertEqual(r.comissoes[0]["comissao_brl"], Decimal("0.00"))
        cond = next(p for p in r.pendencias if p["tipo"] == "CADASTRO_CONDICAO")
        self.assertEqual(cond["valor_brl"], Decimal("26.90"))  # 2,69% da planilha, não os 0% da linha CONFIG
        self.assertEqual(soma_rastro(r, cond["id_saida"]), cond["valor_brl"])

    def test_resultado_nao_depende_da_ordem_das_linhas_de_entrada(self):
        linhas = [transacao("TX3", cnpj=CNPJ_B, bruto="10.00"), transacao("TX1", bruto="1000.00"),
                  transacao("TX9", ec="1076801732", status_ec="RETIDO", bruto="5.00"),
                  transacao("TX2", bruto="-20.00", tipo="ESTORNO", data_venda_original="2026-09-01")]
        contratos = [contrato(), contrato(CNPJ_B, linha="12")]

        a = calcular(entrada(linhas, contratos=contratos))
        b = calcular(entrada(list(reversed(linhas)), contratos=list(reversed(contratos))))

        self.assertEqual((a.comissoes, a.rastro, a.pendencias, a.divergencias),
                         (b.comissoes, b.rastro, b.pendencias, b.divergencias))
        self.assertEqual([c["cnpj"] for c in a.comissoes], sorted(c["cnpj"] for c in a.comissoes))


if __name__ == "__main__":
    unittest.main()
