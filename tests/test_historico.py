"""Histórico dos meses fechados (src.historico): arquivo do mês, trava de mês fechado e o que o mês seguinte herda.
Rodar da raiz: python -m unittest discover -s tests -t ."""
from __future__ import annotations

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from src import fechar, historico
from src.utils import sha256
from src.remessa.regras import Classe, classificar
from tests.remessa.test_remessa import CFG, op

RAIZ = Path(__file__).resolve().parents[1]
INPUT, CONFIG = RAIZ / "input", RAIZ / "config"


def ler(caminho: Path) -> list[dict]:
    with Path(caminho).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def gravar(caminho: Path, linhas: list[dict]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]), delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)


class SetembroArquivado(unittest.TestCase):
    """Fecha setembro de ponta a ponta numa pasta temporária, com arquivo em fechamentos/ temporário."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls.hist = cls.tmp / "fechamentos"
        cls.res = fechar.fechar("2026-09", INPUT, cls.tmp / "data", cls.tmp / "saida", CONFIG,
                                arquivar=True, raiz_hist=cls.hist)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_arquiva_saida_tabelas_e_manifesto(self):
        self.assertTrue(self.res["validador"]["ok"], self.res["validador"]["texto"])
        pasta = self.hist / "2026-09"
        for n in historico.SAIDAS:
            self.assertEqual((pasta / "saida" / f"{n}.csv").read_bytes(), (self.tmp / "saida" / f"{n}.csv").read_bytes(), n)
        for n in historico.TABELAS:
            self.assertTrue((pasta / "data" / f"{n}.csv").exists(), n)
        m = json.loads((pasta / "manifesto.json").read_text(encoding="utf-8"))
        self.assertEqual(m["mes"], "2026-09")
        self.assertEqual(m["totais"]["comissao_total"], "243278.79")
        arquivos = {a["arquivo"]: a["sha256"] for a in m["arquivos_de_entrada"]}
        self.assertEqual(len(arquivos), 7)          # 6 fontes + ajustes tardios da Orbe
        self.assertEqual(arquivos["01_orbe_relatorio_comissoes_set2026.csv"],
                         sha256(INPUT / "01_orbe_relatorio_comissoes_set2026.csv"))
        self.assertEqual(historico.meses_fechados(self.hist), ["2026-09"])

    def test_pendencias_abertas_levam_o_mes_de_origem(self):
        abertas = ler(self.hist / "2026-09" / "pendencias_abertas.csv")
        self.assertEqual(len(abertas), len(ler(self.tmp / "saida" / "pendencias.csv")))
        self.assertEqual({p["mes_origem"] for p in abertas}, {"2026-09"})

    def test_mes_fechado_nao_reabre(self):
        with self.assertRaises(historico.MesFechado):
            fechar.fechar("2026-09", self.tmp / "nao-precisa-existir", self.tmp / "d", self.tmp / "s", CONFIG,
                          arquivar=True, raiz_hist=self.hist)
        with self.assertRaises(historico.MesFechado):
            historico.arquivar("2026-09", self.tmp / "data", self.tmp / "saida", CONFIG, {}, self.hist)

    def test_refazer_guarda_o_fechamento_anterior(self):
        hist = self.tmp / "hist_refazer"
        shutil.copytree(self.hist, hist)
        destino = historico.arquivar("2026-09", self.tmp / "data", self.tmp / "saida", CONFIG, {"x": 1}, hist, refazer=True)
        m = json.loads((destino / "manifesto.json").read_text(encoding="utf-8"))
        self.assertEqual(len(m["anteriores"]), 1)
        guardado = destino / m["anteriores"][0]
        self.assertTrue((guardado / "manifesto.json").exists())
        self.assertTrue((guardado / "saida" / "rastro.csv").exists())

    def test_rastro_arquivado_diz_o_que_ja_foi_faturado(self):
        f = historico.chaves_faturadas(self.hist, antes_de="2026-10")
        self.assertEqual(f["orbe"]["TX88410258"], "2026-09")       # venda da Andes, na comissão de setembro
        self.assertEqual(f["ponte"]["PC-0926-0002"], "2026-09")
        self.assertEqual(historico.chaves_faturadas(self.hist, antes_de="2026-09"), {"orbe": {}, "ponte": {}})

    def test_transacao_da_orbe_ja_faturada_para_o_mes_seguinte(self):
        dados = self.tmp / "outubro_repetido"
        orbe = ler(self.tmp / "data" / "fato_orbe.csv")[:3]       # outubro trazendo de novo linhas de setembro
        gravar(dados / "fato_orbe.csv", orbe)
        with self.assertRaises(historico.CobrancaDuplicada) as e:
            historico.conferir(dados, "2026-10", self.hist)
        self.assertIn(orbe[0]["id_transacao"], str(e.exception))

    def test_operacao_da_ponte_ja_faturada_conta_uma_vez(self):
        dados = self.tmp / "outubro_ponte"
        gravar(dados / "fato_orbe.csv", [{"id_transacao": "TX99999999"}])
        ponte = [l for l in ler(self.tmp / "data" / "fato_ponte.csv") if l["num_op"] == "PC-0926-0002"]
        gravar(dados / "fato_ponte.csv", ponte)
        ja = historico.conferir(dados, "2026-10", self.hist)
        self.assertEqual(ja, {"PC-0926-0002": "2026-09"})
        o = op(num="PC-0926-0002", data="2026-09-30")
        self.assertIs(classificar(o, "2026-10", CFG, frozenset(ja)).classe, Classe.JA_FATURADA)
        self.assertIs(classificar(o, "2026-10", CFG).classe, Classe.FORA_COMPETENCIA)   # sem histórico: continua pendência

    def test_outubro_herda_as_pendencias_abertas_menos_as_resolvidas(self):
        total = len(ler(self.tmp / "saida" / "pendencias.csv"))
        self.assertEqual(len(historico.pendencias_herdadas("2026-10", CONFIG, self.hist)), total)
        self.assertEqual(historico.pendencias_herdadas("2026-09", CONFIG, self.hist), [])
        config = self.tmp / "config_resolvida"
        config.mkdir()
        gravar(config / "pendencias_resolvidas.csv",
               [{"id_saida": "PEN-BCO-2026-09-PIX_SEM_IDENTIFICACAO-L50", "resolvido_em": "2026-10-05",
                 "decisao": "identificado", "quem_decidiu": "Helena"}])
        herdadas = historico.pendencias_herdadas("2026-10", config, self.hist)
        self.assertEqual(len(herdadas), total - 1)
        self.assertNotIn("PEN-BCO-2026-09-PIX_SEM_IDENTIFICACAO-L50", {p["id_saida"] for p in herdadas})


class MesAnterior(unittest.TestCase):
    def test_vira_o_ano(self):
        self.assertEqual(historico.mes_anterior("2026-10"), "2026-09")
        self.assertEqual(historico.mes_anterior("2027-01"), "2026-12")


if __name__ == "__main__":
    unittest.main()


class RodadaQueFalha(unittest.TestCase):
    """Uma rodada que para no meio não pode deixar data/ e saida/ pela metade (antes, a ingestão já tinha gravado)."""

    @staticmethod
    def fotografia(pasta: Path) -> dict[str, bytes]:
        return {str(p.relative_to(pasta)): p.read_bytes() for p in sorted(pasta.rglob("*")) if p.is_file()}

    def test_competencia_errada_nao_altera_data_nem_saida(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            dados, saida = tmp / "data", tmp / "saida"
            fechar.fechar("2026-09", INPUT, dados, saida, CONFIG, raiz_hist=tmp / "fechamentos")
            antes = (self.fotografia(dados), self.fotografia(saida))
            self.assertIn("fato_orbe.csv", antes[0])
            with self.assertRaises(fechar.CompetenciaDivergente):          # arquivos de setembro pedidos como outubro
                fechar.fechar("2026-10", INPUT, dados, saida, CONFIG, arquivar=True, raiz_hist=tmp / "fechamentos")
            self.assertEqual((self.fotografia(dados), self.fotografia(saida)), antes)
            self.assertFalse(historico.esta_fechado("2026-10", tmp / "fechamentos"))

    def test_rodada_que_passa_publica_nas_pastas_de_destino(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            res = fechar.fechar("2026-09", INPUT, tmp / "data", tmp / "saida", CONFIG, raiz_hist=tmp / "fechamentos")
            self.assertTrue(res["validador"]["ok"])
            for n in historico.SAIDAS:
                self.assertTrue((tmp / "saida" / f"{n}.csv").exists(), n)
            for sub in ("checkouts", "parcial"):
                self.assertTrue((tmp / "saida" / sub).is_dir(), sub)
            self.assertTrue((tmp / "data" / "fato_orbe.csv").exists())
