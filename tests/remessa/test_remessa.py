"""Testes do módulo de remessa. Rodar da raiz: python -m unittest discover -s tests -t . """
from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from src.remessa.comissao import calcular_comissoes
from src.remessa.ids import id_comissao, id_divergencia, id_nota, id_pendencia
from src.remessa.nota import montar_nota
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

    def test_ajuste_de_setembro_rodando_em_outubro_entra_no_mes_em_que_aparece(self):
        """O ajuste vem no relatório de outubro com data de contratação de 28/09: não é fora de competência."""
        c = classificar(op(data="2026-09-28", spread="-50", obs="AJUSTE REF PC-0926-0042"), "2026-10", CFG)
        self.assertIs(c.classe, Classe.AJUSTE)
        self.assertEqual(c.op_original, "PC-0926-0042")

    def test_operacao_normal_de_setembro_rodando_em_outubro_continua_fora(self):
        """Só o ajuste atravessa o mês; uma operação normal de 28/09 no relatório de outubro fica de fora."""
        self.assertIs(classificar(op(data="2026-09-28"), "2026-10", CFG).classe, Classe.FORA_COMPETENCIA)

    def test_ajuste_de_setembro_em_outubro_abate_a_participacao_do_mes(self):
        normal = classificar(op(num="PC-1026-0001", data="2026-10-05", spread="100"), "2026-10", CFG)
        ajuste = classificar(op(num="PC-1026-0002", data="2026-09-28", spread="-50", obs="AJUSTE REF PC-0926-0042"),
                             "2026-10", CFG)
        linhas, rastro, _ = calcular_comissoes([normal, ajuste], {}, CFG, "2026-10")
        self.assertEqual(linhas[0]["comissao_brl"], D("25.00"))            # 50,00 - 25,00
        self.assertEqual(sum(r["valor"] for r in rastro), D("25.00"))
        self.assertEqual({r["ref_original"] for r in rastro} - {""}, {"PC-0926-0042"})


class Comissao(unittest.TestCase):
    def test_metade_do_spread_arredondada_por_operacao(self):
        cls = [classificar(op(num="A", spread="262.01"), "2026-09", CFG),
               classificar(op(num="B", spread="262.01"), "2026-09", CFG)]
        linhas, _, por_op = calcular_comissoes(cls, {}, CFG, "2026-09")
        self.assertEqual(por_op["A"], D("131.01"))
        self.assertEqual(linhas[0]["comissao_brl"], D("262.02"))

    def test_so_elegiveis_entram_e_ajuste_abate(self):
        cls = [classificar(op(num="A", spread="100"), "2026-09", CFG),
               classificar(op(num="N", spread="-40"), "2026-09", CFG),
               classificar(op(num="D", spread="100", dup=True), "2026-09", CFG),
               classificar(op(num="J", spread="-20", obs="AJUSTE REF PC-0826-0001"), "2026-09", CFG)]
        linhas, rastro, _ = calcular_comissoes(cls, {}, CFG, "2026-09")
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
        cfg = replace(CFG, tolerancia_brl=D("0"), tolerancia_pp=D("0"))
        dif, _ = calcular_diferencas([classificar(op(spread="75.01"), "2026-09", cfg)], por_cnpj, cfg)
        linhas, _ = divergencias(dif, cfg, "2026-09")
        self.assertEqual(len(linhas), 1)

    def test_tolerancia_em_pp_ignora_ruido_e_mantem_divergencia_real(self):
        por_cnpj = indexar_contratos([contrato(pct="1.5")])
        cfg = replace(CFG, tolerancia_pp=D("0.005"))
        ruido = classificar(op(num="R", spread="75.30"), "2026-09", CFG)   # +0,006 p.p. sobre base 5000 -> acima
        micro = classificar(op(num="M", spread="75.20"), "2026-09", CFG)   # +0,004 p.p. -> dentro do ruido
        real = classificar(op(num="V", spread="150"), "2026-09", CFG)      # +1,5 p.p.
        dif, _ = calcular_diferencas([ruido, micro, real], por_cnpj, cfg)
        linhas, _ = divergencias(dif, cfg, "2026-09")
        self.assertEqual({l["ref_origem"] for l in linhas}, {"R", "V"})

    def test_tolerancia_vale_so_quando_ultrapassa_as_duas(self):
        por_cnpj = indexar_contratos([contrato(pct="1.5")])
        cfg = replace(CFG, tolerancia_brl=D("100"))   # diferença de 75 fica dentro da tolerância em reais
        dif, _ = calcular_diferencas([classificar(op(spread="150"), "2026-09", CFG)], por_cnpj, cfg)
        self.assertEqual(divergencias(dif, cfg, "2026-09")[0], [])

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


class Ids(unittest.TestCase):
    def test_formato_igual_ao_do_checkout(self):
        self.assertEqual(id_comissao("2026-09", "34671260000100"), "REM-2026-09-34671260000100")
        self.assertEqual(id_divergencia("2026-09", "PC-0926-0011"), "DIV-REM-2026-09-PC-0926-0011")
        self.assertEqual(id_pendencia("2026-09", "DUPLICATA", "PC-0926-0162"), "PEN-REM-2026-09-DUPLICATA-PC-0926-0162")
        self.assertEqual(id_nota("2026-09", "75374179000146"), "NF-REM-2026-09-75374179000146")


class Nota(unittest.TestCase):
    def test_uma_nota_com_o_total_e_rastro_por_operacao(self):
        cls = [classificar(op(num="A", spread="100"), "2026-09", CFG), classificar(op(num="B", spread="50"), "2026-09", CFG)]
        linhas, rastro_com, _ = calcular_comissoes(cls, {}, CFG, "2026-09")
        notas, rastro = montar_nota(D("75.00"), rastro_com, "2026-09", CFG)
        self.assertEqual(len(notas), 1)
        self.assertEqual((notas[0]["tomador_cnpj"], notas[0]["valor_brl"]), ("75374179000146", D("75.00")))
        self.assertIn("09/2026", notas[0]["discriminacao"])
        self.assertEqual(sum(r["valor"] for r in rastro), D("75.00"))
        self.assertEqual({r["id_saida"] for r in rastro}, {notas[0]["id_saida"]})

    def test_zero_ou_negativo_nao_emite(self):
        self.assertEqual(montar_nota(D("0.00"), [], "2026-09", CFG), ([], []))
        self.assertEqual(montar_nota(D("-10.00"), [], "2026-09", CFG), ([], []))


class AjusteNoFechamento(unittest.TestCase):
    """Setembro não tem ajuste da Ponte. Acrescenta uma linha sintética AJUSTE REF ao fato_ponte e roda o pipeline inteiro."""

    def test_ajuste_abate_a_participacao_e_o_rastro_aponta_para_a_original(self):
        import csv
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            dados = Path(tmp) / "data"
            shutil.copytree(RAIZ / "data", dados)
            with (dados / "fato_ponte.csv").open(encoding="utf-8", newline="") as f:
                leitor = csv.DictReader(f, delimiter=";")
                colunas, linhas = leitor.fieldnames, list(leitor)
            ajuste = dict(linhas[0], num_op="PC-0926-9999", spread_brl="-100.00", spread_pct="-0.5", flag_spread_negativo="S",
                          observacao="AJUSTE REF PC-0826-0042", linha_origem="999")
            with (dados / "fato_ponte.csv").open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=colunas, delimiter=";", lineterminator="\n")
                w.writeheader(); w.writerows(linhas + [ajuste])
            saida = Path(tmp) / "saida"
            executar("2026-09", dados, saida, RAIZ / "config" / "remessa.json")
            resumo = {l.split(";")[0]: l.strip().split(";")[1]
                      for l in (saida / "remessa_resumo.csv").read_text(encoding="utf-8").splitlines()[1:]}
            rastro = list(csv.DictReader((saida / "remessa_rastro.csv").read_text(encoding="utf-8").splitlines(), delimiter=";"))
            notas = list(csv.DictReader((saida / "remessa_notas.csv").read_text(encoding="utf-8").splitlines(), delimiter=";"))
        self.assertEqual(resumo["operacoes_ajuste"], "1")
        self.assertEqual(resumo["total_participacao_brl"], "39493.45")        # 39543,45 - 50
        self.assertEqual(notas[0]["valor_brl"], "39493.45")
        linha = next(r for r in rastro if r["ref_origem"] == "PC-0926-9999" and r["id_saida"].startswith("REM-"))
        self.assertEqual((linha["valor"], linha["ref_original"]), ("-50.00", "PC-0826-0042"))


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
