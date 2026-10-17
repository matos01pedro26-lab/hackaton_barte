"""Testes do comando único (src.fechar) e da tela (src.app). Rodar da raiz: python -m unittest discover -s tests -t ."""
from __future__ import annotations

import http.client
import io
import json
import shutil
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path

from src import app, fechar

RAIZ = Path(__file__).resolve().parents[1]
INPUT = RAIZ / "input"


class ComandoUnico(unittest.TestCase):
    def test_fecha_setembro_e_gera_os_seis_arquivos(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            res = fechar.fechar("2026-09", INPUT, tmp / "data", tmp / "saida", RAIZ / "config")
            self.assertTrue(res["validador"]["ok"], res["validador"]["texto"])
            for n in fechar.SAIDAS:
                self.assertTrue((tmp / "saida" / f"{n}.csv").exists(), n)
            k = fechar.resumir(tmp / "saida", tmp / "data")["kpis"]
        self.assertEqual(k["comissao_remessa"], "39543.45")
        self.assertEqual(k["notas_qtd"], 21)
        self.assertEqual(k["lancamentos_qtd"], 184)

    def test_mes_invalido_e_arquivos_faltando_param_com_mensagem(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            with self.assertRaises(ValueError):
                fechar.fechar("setembro", INPUT, tmp / "d", tmp / "s", RAIZ / "config")
            (tmp / "vazia").mkdir()
            with self.assertRaises(fechar.EntradaIncompleta) as e:
                fechar.fechar("2026-09", tmp / "vazia", tmp / "d", tmp / "s", RAIZ / "config")
            self.assertIn("01_orbe", str(e.exception))

    def test_mes_que_nao_bate_com_as_datas_dos_arquivos_para_com_aviso(self):
        """Pedir outubro com arquivos de setembro não pode calcular em silêncio."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            with self.assertRaises(fechar.CompetenciaDivergente) as e:
                fechar.fechar("2026-10", INPUT, tmp / "data", tmp / "saida", RAIZ / "config")
        self.assertIn("2026-09", str(e.exception))
        self.assertIn("2026-10", str(e.exception))

    def test_infere_o_mes_pelos_nomes(self):
        self.assertEqual(fechar.inferir_mes(["01_orbe_relatorio_comissoes_set2026.csv", "06_orbe_ajustes_tardios_set2026.csv"]), "2026-09")
        self.assertEqual(fechar.inferir_mes(["01_orbe_out2026.csv"]), "2026-10")
        self.assertIsNone(fechar.inferir_mes(["sem_mes.csv"]))

    def test_formato_brasileiro(self):
        self.assertEqual(fechar.brl("1234.5"), "R$ 1.234,50")
        self.assertEqual(fechar.brl("-5.5"), "-R$ 5,50")


def multipart(campos: dict[str, str], arquivos: list[tuple[str, bytes]]) -> tuple[bytes, str]:
    f = "----fronteiraDeTeste"
    corpo = b""
    for k, v in campos.items():
        corpo += f'--{f}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for nome, dados in arquivos:
        corpo += f'--{f}\r\nContent-Disposition: form-data; name="arquivo"; filename="{nome}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode() + dados + b"\r\n"
    return corpo + f"--{f}--\r\n".encode(), f"multipart/form-data; boundary={f}"


class Tela(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._exec = tempfile.mkdtemp()
        app.EXECUCOES = Path(cls._exec)        # as rodadas do teste não sujam execucoes/ do repositório
        cls.srv = app.criar_servidor(0)
        cls.porta = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); cls.srv.server_close()
        shutil.rmtree(cls._exec, ignore_errors=True)

    def chamar(self, metodo, caminho, corpo=None, tipo=None):
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=60)
        c.request(metodo, caminho, body=corpo, headers={"Content-Type": tipo} if tipo else {})
        r = c.getresponse(); dados = r.read(); c.close()
        return r.status, r.getheader("Content-Type"), dados

    def rodar(self, campos, arquivos=()):
        corpo, tipo = multipart(campos, list(arquivos))
        status, _, dados = self.chamar("POST", "/api/fechar", corpo, tipo)
        return status, json.loads(dados)

    def test_pagina_e_estado(self):
        status, tipo, dados = self.chamar("GET", "/")
        self.assertEqual(status, 200); self.assertIn("text/html", tipo); self.assertIn("Fechamento", dados.decode())
        status, _, dados = self.chamar("GET", "/api/estado")
        e = json.loads(dados)
        self.assertEqual(e["mes_sugerido"], "2026-09"); self.assertEqual(len(e["fontes"]), 6)

    def test_upload_dos_arquivos_roda_e_o_rastro_fecha(self):
        arquivos = [(p.name, p.read_bytes()) for p in sorted(INPUT.glob("*")) if p.is_file()]
        status, r = self.rodar({"mes": "2026-09", "origem": "upload"}, arquivos)
        self.assertEqual(status, 200, r)
        self.assertTrue(r["validador"]["ok"])
        self.assertEqual(r["kpis"]["comissao_total"], "243278.79")
        self.assertEqual([a["nome"] for a in r["arquivos"]], [f"{n}.csv" for n in fechar.SAIDAS])
        # rastro de um número da tela
        com = next(c for c in r["comissoes"] if c["linha_negocio"] == "REMESSA")
        status, _, dados = self.chamar("GET", f"/api/rastro?e={r['id']}&id={com['id_saida']}")
        rastro = json.loads(dados)
        self.assertEqual(status, 200); self.assertTrue(rastro["fecha"]); self.assertGreater(rastro["total_linhas"], 0)
        # downloads
        status, tipo, dados = self.chamar("GET", f"/baixar/{r['id']}/comissoes_por_lojista.csv")
        self.assertEqual(status, 200); self.assertTrue(dados.decode().startswith("id_saida;cnpj;lojista;linha_negocio;comissao_brl"))
        status, _, dados = self.chamar("GET", f"/baixar/{r['id']}/saidas.zip")
        self.assertEqual(sorted(zipfile.ZipFile(io.BytesIO(dados)).namelist()), sorted(f"saida/{n}.csv" for n in fechar.SAIDAS))

    def test_usar_os_arquivos_do_case(self):
        status, r = self.rodar({"mes": "2026-09", "origem": "exemplo"})
        self.assertEqual(status, 200, r); self.assertEqual(r["kpis"]["notas_qtd"], 21)

    def test_arquivo_faltando_avisa_o_que_falta_e_nao_calcula(self):
        arquivos = [(p.name, p.read_bytes()) for p in sorted(INPUT.glob("*")) if p.is_file() and not p.name.startswith("03_")]
        status, r = self.rodar({"mes": "2026-09", "origem": "upload"}, arquivos)
        self.assertEqual(status, 422)
        self.assertTrue(any("03_email_ponte" in f for f in r["faltam"]), r)

    def test_competencia_errada_na_tela_avisa_e_nao_calcula(self):
        status, r = self.rodar({"mes": "2026-10", "origem": "exemplo"})
        self.assertEqual(status, 422)
        self.assertIn("não parecem ser de 2026-10", r["erro"])

    def test_mes_invalido(self):
        status, r = self.rodar({"mes": "setembro", "origem": "exemplo"})
        self.assertEqual(status, 422); self.assertIn("AAAA-MM", r["erro"])

    def test_nome_de_arquivo_perigoso_e_ignorado_e_nunca_sai_da_pasta(self):
        arquivos = [(p.name, p.read_bytes()) for p in sorted(INPUT.glob("*")) if p.is_file()]
        arquivos += [("../../fora.csv", b"x"), ("..\\..\\fora2.csv", b"x"), ("script.py", b"x")]
        status, r = self.rodar({"mes": "2026-09", "origem": "upload"}, arquivos)
        self.assertEqual(status, 200, r)
        self.assertEqual(len(r["rejeitados"]), 3, r["rejeitados"])                 # os três nomes fora do padrão
        self.assertIn("script.py", r["rejeitados"])
        self.assertTrue(all(n.startswith("0") for n in r["enviados"]), r["enviados"])  # só entrou o que segue o padrão 01..06
        for nome in ("fora.csv", "fora2.csv"):
            self.assertFalse((Path(self._exec).parent / nome).exists())
            self.assertFalse((Path(self._exec) / nome).exists())

    def test_download_so_aceita_os_seis_arquivos(self):
        status, r = self.rodar({"mes": "2026-09", "origem": "exemplo"})
        for nome in ("../resumo.json", "resumo.json", "..%2F..%2Fsrc%2Fapp.py"):
            status, _, _ = self.chamar("GET", f"/baixar/{r['id']}/{nome}")
            self.assertEqual(status, 404, nome)
        status, _, _ = self.chamar("GET", "/baixar/..%2F..%2F/saidas.zip")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
