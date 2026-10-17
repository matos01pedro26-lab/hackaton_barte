"""Gera um mês sintético (outubro) a partir do set de setembro, para testar se o fechamento roda num mês novo.

O que muda: todas as datas andam 30 dias (extratos, Orbe, Ponte, tabela de taxas), os nomes dos arquivos viram `out2026`
e os IDs de transação ganham outro prefixo (o guarda de refaturamento bloqueia IDs já faturados em setembro).
O que não muda: valores, taxas, CNPJs, ECs e a lógica. Nada de `input/` é alterado; tudo é gravado na pasta que você passar.

Uso (a partir da raiz): python -m tests.mes_sintetico <pasta_destino>
"""
from __future__ import annotations

import base64
import datetime as dt
import email
import io
import re
import shutil
import sys
import zipfile
from email import policy
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = RAIZ / "input"
DELTA = dt.timedelta(days=30)

# nome do arquivo de setembro -> nome do arquivo de outubro
NOMES = {
    "01_orbe_relatorio_comissoes_set2026.csv": "01_orbe_relatorio_comissoes_out2026.csv",
    "06_orbe_ajustes_tardios_set2026.csv": "06_orbe_ajustes_tardios_out2026.csv",
    "03_email_ponte_cambio_relatorio_set2026.eml": "03_email_ponte_cambio_relatorio_out2026.eml",
    "05a_extrato_banco_aurora_cc4471_set2026.csv": "05a_extrato_banco_aurora_cc4471_out2026.csv",
    "05b_extrato_banco_meridiano_cc90233_set2026.ofx": "05b_extrato_banco_meridiano_cc90233_out2026.ofx",
    "02_tabela_taxas_contratadas.xlsx": "02_tabela_taxas_contratadas.xlsx",
    "04_plano_de_contas_fenix_erp.csv": "04_plano_de_contas_fenix_erp.csv",
}


def _mais30_br(m: re.Match) -> str:
    d = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))) + DELTA
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def _mais30_ofx(m: re.Match) -> str:
    return f"{(dt.datetime.strptime(m.group(2), '%Y%m%d').date() + DELTA):%Y%m%d}"


def _texto(s: str) -> str:
    s = re.sub(r"(\d{2})/(\d{2})/(2026)", _mais30_br, s)
    s = s.replace("Período: 01/09/2026", "Período: 01/10/2026")
    s = s.replace("competência 09/2026", "competência 10/2026").replace("Competência: 09/2026", "Competência: 10/2026")
    s = s.replace("09/2026", "10/2026")
    return s.replace("TX88", "TZ88").replace("AN88", "AZ88")


def _xlsx_setembro_para_outubro(dados: bytes, em_taxas: bool) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(dados)) as zin, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            conteudo = zin.read(info.filename)
            if info.filename.startswith("xl/worksheets/sheet"):
                t = conteudo.decode("utf-8")
                if em_taxas:
                    t = re.sub(r"(\d{2})/(\d{2})/(2026)", _mais30_br, t)
                else:
                    # relatório da Ponte: datas são números de série do Excel (linhas de dados a partir da 6)
                    t = re.sub(r'(<c r="[BC](\d+)" s="3" t="n"><v>)(\d+)(</v>)',
                               lambda m: m.group(1) + (str(int(m.group(3)) + 30) if int(m.group(2)) >= 6 else m.group(3))
                               + m.group(4), t)
                    t = t.replace("Compet&#234;ncia: 09/2026", "Compet&#234;ncia: 10/2026")
                    t = re.sub(r"Gerado em \d{2}/\d{2}/2026", "Gerado em 02/11/2026", t)
                    t = t.replace("PC-0926-", "PC-1026-")
                conteudo = t.encode("utf-8")
            zout.writestr(info, conteudo)
    return buf.getvalue()


def gerar(destino: Path) -> Path:
    """Escreve o set de outubro em `destino` (cria a pasta). Devolve a pasta."""
    destino.mkdir(parents=True, exist_ok=True)
    for origem, novo in NOMES.items():
        bruto = (ORIGEM / origem).read_bytes()
        if origem.endswith(".xlsx"):
            saida = _xlsx_setembro_para_outubro(bruto, em_taxas=(origem.startswith("02_")))
        elif origem.endswith(".ofx"):
            saida = re.sub(r"(<DT[A-Z]+>)(2026\d{4})", lambda m: m.group(1) + _mais30_ofx(m),
                           bruto.decode("cp1252")).encode("cp1252")
        elif origem.endswith(".eml"):
            msg = email.message_from_bytes(bruto, policy=policy.compat32)
            for part in msg.walk():
                if part.get_content_type().endswith("spreadsheetml.sheet"):
                    novo_xlsx = _xlsx_setembro_para_outubro(part.get_payload(decode=True), em_taxas=False)
                    part.set_payload(base64.encodebytes(novo_xlsx).decode("ascii"))
                elif part.get_content_maintype() == "text" and part.get_content_subtype() == "plain":
                    corpo = _texto(part.get_payload(decode=True).decode("utf-8"))
                    part.set_payload(base64.encodebytes(corpo.encode("utf-8")).decode("ascii"))
                    part["Content-Transfer-Encoding"] = "base64"
            msg.replace_header("Date", "Mon, 02 Nov 2026 07:15:03 -0300")
            msg.replace_header("Subject", str(msg["Subject"]).replace("09/2026", "10/2026"))
            saida = msg.as_bytes(policy=policy.compat32)
        elif origem.endswith(".csv") and origem.startswith(("01_", "06_", "05a_")):
            saida = _texto(bruto.decode("utf-8")).encode("utf-8")
        else:
            saida = bruto
        (destino / novo).write_bytes(saida)
    return destino


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("uso: python -m tests.mes_sintetico <pasta_destino>")
    print("outubro sintético em", gerar(Path(sys.argv[1])))
