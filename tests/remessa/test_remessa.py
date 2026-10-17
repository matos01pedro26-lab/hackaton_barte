"""Testes do módulo de remessa. Rodar da raiz: python -m unittest discover -s tests -t . """
from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from src.remessa.comissao import calcular_comissoes
from src.remessa.config import carregar_config
from src.remessa.divergencia import calcular_diferencas, divergencias
from src.remessa.leitura import Contrato, Operacao
from src.remessa.pipeline import executar
from src.remessa.regras import Classe, arredondar, classificar, contrato_vigente, indexar_contratos
from src.remessa.saida import validar_rastro

RAIZ = Path(__file__).resolve().parents[2]
CFG = carregar_config(RAIZ / "config" / "remessa.json")
D = Decimal


def op(num="PC-0926-0001", cnpj="11111111000111", data="2026-09-10", me="1000", ptax="5", spread="100",
       obs="", dup=False, pct="2") -> Operacao:
    return Operacao(num, "arq", "6", data, cnpj, "CLIENTE", D(me), D(ptax), D(spread), D(pct), "APROVADO", obs, dup)


def contrato(cnpj="11111111000111", pct="1.5", ini="", fim="") -> Contrato:
    return Contrato(cnpj, "Lojista", ini, fim, None if pct is None else D(pct), "EXPLICITO" if pct else "PADRAO")


class Arredondamento(unittest.TestCase):
    def test_meio_centavo_vai_para_longe_do_zero(self):
        self.assertEqual(arredondar(D("131.005")), D("131.01"))
        self.assertEqual(arredondar(D("-0.005")), D("-0.01"))
        self.assertEqual(arredondar(D("0.004")), D("0.00"))


class Classificacao(unittest.TestCase):
    def test_normal(self):
        self.assertIs(classificar(op(), "2026-09", CFG).classe, Classe.NORMAL)

    def test_status_ressalva_nao_muda_nada(self):
        self.assertIs(classificar(op(), "2026-09", CFG).classe, Classe.NORMAL)

    def test_duplicata_vem_primeiro(self):
        self.assertIs(classificar(op(dup=True, spread="-5"), "2026-09", CFG).classe, Classe.DUPLICATA)

    def test_spread_negativo(self):
        self.assertIs(classificar(op(spread="-687.52", obs="Taxa travada no pedido (D-1)"), "2026-09", CFG).classe,
                      Classe.SPREAD_NEGATIVO)

    def test_ajuste_negativo_nao_e_spread_negativo(self):
        c = classificar(op(spread="-50", obs="AJUSTE REF PC-0826-0099"), "2026-09", CFG)
        self.assertIs(c.classe, Classe.AJUSTE)
        self.assertEqual(c.op_original, "PC-0826-0099")

    def test_data_de_contratacao_fora_do_mes(self):
        self.assertIs(classificar(op(data="2026-08-31"), "2026-09", CFG).classe, Classe.FORA_COMPETENCIA)

    def test_liquidacao_em_outubro_vale_pela_contratacao(self):
        self.assertIs(classificar(op(data="2026-09-30"), "2026-09", CFG).classe, Classe.NORMAL)


class Comissao(unittest.TestCase):
    def test_metade_do_spread_arredondada_por_operacao(self):
        cls = [classificar(op(num="A", spread="262.01"), "2026-09", CFG),
               classificar(op(num="B", spread="262.01"), "2026-09", CFG)]
        linhas, _, por_op = calcular_comissoes(cls, {}, CFG)
        self.assertEqual(por_op["A"], D("131.01"))
        self.assertEqual(linhas[0]["comissao_brl"], D("262.02"))

    def test_so_elegiveis_entram_e_ajuste_abate(self):
        cls = [classificar(op(num="A", spread="100"), "2026-09", CFG),
               classificar(op(num="N", spread="-40"), "2026-09", CFG),
               classificar(op(num="D", spread="100", dup=True), "2026-09", CFG),
               classificar(op(num="J", spread="-20", obs="AJUSTE REF PC-0826-0001"), "2026-09", CFG)]
        linhas, rastro, _ = calcular_comissoes(cls, {}, CFG)
        self.assertEqual(linhas[0]["comissao_brl"], D("40.00"))
        self.assertEqual({r["ref_origem"] for r in rastro}, {"A", "J"})
        self.assertEqual([r["ref_original"] for r in rastro if r["ref_origem"] == "J"], ["PC-0826-0001"])


class Divergencia(unittest.TestCase):
    def test_diferenca_e_valor_cheio_contra_o_contrato(self):
        # spread aplicado 150 sobre base 1000*5=5000 (3%); contratado 1,5% = 75; diferença cheia = 75
        por_cnpj = indexar_contratos([contrato(pct="1.5")])
        dif, sem = calcular_diferencas([classificar(op(spread="150"), "2026-09", CFG)], por_cnpj, CFG)
        self.assertEqual(sem, [])
        self.assertEqual(dif[0].diferenca_brl, D("75.00"))

    def test_spread_em_branco_usa_padrao(self):
        por_cnpj = indexar_contratos([contrato(pct=None)])
        dif, _ = calcular_diferencas([classificar(op(spread="75"), "2026-09", CFG)], por_cnpj, CFG)
        self.assertEqual((dif[0].contratado_pct, dif[0].regra, dif[0].diferenca_brl), (D("1.5"), "PADRAO", D("0.00")))

    def test_spread_negativo_tem_diferenca_ate_o_contrato(self):
        por_cnpj = indexar_contratos([contrato(pct="1.5")])
        dif, _ = calcular_diferencas([classificar(op(spread="-10"), "2026-09", CFG)], por_cnpj, CFG)
        self.assertEqual(dif[0].diferenca_brl, D("-85.00"))

    def test_tolerancia_zero_reporta_qualquer_centavo(self):
        por_cnpj = indexar_contratos([contrato(pct="1.5")])
        dif, _ = calcular_diferencas([classificar(op(spread="75.01"), "2026-09", CFG)], por_cnpj, CFG)
        linhas, _ = divergencias(dif, CFG)
        self.assertEqual(len(linhas), 1)

    def test_tolerancia_em_pp_ignora_ruido_e_mantem_divergencia_real(self):
        por_cnpj = indexar_contratos([contrato(pct="1.5")])
        cfg = replace(CFG, tolerancia_pp=D("0.005"))
        ruido = classificar(op(num="R", spread="75.30"), "2026-09", CFG)   # +0,006 p.p. sobre base 5000 -> acima
        micro = classificar(op(num="M", spread="75.20"), "2026-09", CFG)   # +0,004 p.p. -> dentro do ruido
        real = classificar(op(num="V", spread="150"), "2026-09", CFG)      # +1,5 p.p.
        dif, _ = calcular_diferencas([ruido, micro, real], por_cnpj, cfg)
        linhas, _ = divergencias(dif, cfg)
        self.assertEqual({l["ref_origem"] for l in linhas}, {"R", "V"})

    def test_tolerancia_vale_so_quando_ultrapassa_as_duas(self):
        por_cnpj = indexar_contratos([contrato(pct="1.5")])
        cfg = replace(CFG, tolerancia_brl=D("100"))   # diferença de 75 fica dentro da tolerância em reais
        dif, _ = calcular_diferencas([classificar(op(spread="150"), "2026-09", CFG)], por_cnpj, cfg)
        self.assertEqual(divergencias(dif, cfg)[0], [])

    def test_sem_contrato_vigente_vai_para_cadastro(self):
        dif, sem = calcular_diferencas([classificar(op(), "2026-09", CFG)], {}, CFG)
        self.assertEqual((dif, len(sem)), ([], 1))

    def test_vigencia_inclusiva_nos_limites(self):
        por_cnpj = indexar_contratos([contrato(ini="2026-09-15"), contrato(pct="9", fim="2026-09-14")])
        self.assertEqual(contrato_vigente(op(data="2026-09-14"), por_cnpj).spread_remessa_pct, D("9"))
        self.assertEqual(contrato_vigente(op(data="2026-09-15"), por_cnpj).spread_remessa_pct, D("1.5"))


class Rastro(unittest.TestCase):
    def test_rastro_que_nao_fecha_levanta_erro(self):
        with self.assertRaises(ValueError):
            validar_rastro({"x": ([{"id_saida": "A", "v": D("10.00")}], "v")},
                           [{"id_saida": "A", "valor": D("9.99")}])

    def test_rastro_que_fecha_passa(self):
        validar_rastro({"x": ([{"id_saida": "A", "v": D("10.00")}], "v")},
                       [{"id_saida": "A", "valor": D("4.00")}, {"id_saida": "A", "valor": D("6.00")}])


class PontaAPonta(unittest.TestCase):
    def test_setembro_fecha_com_o_valor_conferido(self):
        with tempfile.TemporaryDirectory() as tmp:
            executar("2026-09", RAIZ / "data", Path(tmp), RAIZ / "config" / "remessa.json")
            resumo = {l.split(";")[0]: l.strip().split(";")[1]
                      for l in (Path(tmp) / "remessa_resumo.csv").read_text(encoding="utf-8").splitlines()[1:]}
        self.assertEqual(resumo["total_participacao_brl"], "39543.45")
        self.assertEqual(resumo["operacoes_spread_negativo"], "4")
        self.assertEqual(resumo["operacoes_duplicata"], "1")


if __name__ == "__main__":
    unittest.main()
