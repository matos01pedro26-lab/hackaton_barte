"""O que garante que o fechamento não está preso a setembro: data do e-mail, pendências por mês e trava de competência."""
from __future__ import annotations

import unittest
from datetime import date

from src import consolidar


class PrazoDaPonte(unittest.TestCase):
    def test_conta_cinco_dias_uteis_a_partir_da_data_do_email(self):
        self.assertIn("e-mail da Ponte de 02/10", consolidar.prazo_ponte(date(2026, 10, 2)))   # sexta: vence na sexta seguinte
        self.assertIn("até 09/10", consolidar.prazo_ponte(date(2026, 10, 2)))
        self.assertIn("e-mail da Ponte de 02/11", consolidar.prazo_ponte(date(2026, 11, 2)))   # outro mês, outra data

    def test_sem_data_do_email_nao_inventa_a_de_setembro(self):
        texto = consolidar.prazo_ponte(None)
        self.assertNotIn("02/10", texto)
        self.assertIn("a confirmar", texto)


class PendenciasDeBancoPorMes(unittest.TestCase):
    FATO = [{"banco": "AURORA", "ref_origem": "L9", "data": "2026-10-01", "saldo": "10.00", "valor": "10.00", "arquivo_origem": "x"}]
    LINHA = {"tipo": "PIX_SEM_IDENTIFICACAO", "banco": "AURORA", "ref_origem": "L50", "motivo": "m", "quem_decide": "h", "mes": "2026-09"}

    def test_linha_de_setembro_nao_vale_em_outubro(self):
        self.assertEqual(consolidar.pendencias_bancos([self.LINHA], self.FATO, "2026-10"), ([], []))

    def test_linha_do_proprio_mes_com_referencia_inexistente_continua_sendo_erro(self):
        with self.assertRaises(ValueError):
            consolidar.pendencias_bancos([self.LINHA], self.FATO, "2026-09")


if __name__ == "__main__":
    unittest.main()
