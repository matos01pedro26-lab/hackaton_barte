"""Tela do fechamento: recebe os arquivos do mês, roda tudo com um clique, mostra o resultado e entrega os seis CSVs.

Uso (a partir da raiz do repositório):
    python -m src.app                 # abre http://127.0.0.1:8765 no navegador
    python -m src.app --porta 9000 --sem-navegador

Roda no computador de quem executa (o endereço 127.0.0.1 é "esta máquina"): só biblioteca padrão do Python, sem instalar nada
e sem chave de API. Cada rodada grava em execucoes/<mês>_<hora>/ e nunca mexe no saida/ entregue.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import shutil
import sys
import threading
import traceback
import webbrowser
import zipfile
from datetime import datetime
from email.parser import BytesParser
from email.policy import HTTP
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from . import fechar as fechamento
from .fechar import FONTES, RAIZ, SAIDAS, EntradaIncompleta

PAGINA = RAIZ / "src" / "web" / "index.html"
EXECUCOES = RAIZ / "execucoes"
ENTRADA_CASE = RAIZ / "input"
NOME_VALIDO = re.compile(r"^0[1-6][ab]?_[A-Za-z0-9_.\-]+\.(csv|xlsx|eml|ofx)$")
ID_EXECUCAO = re.compile(r"^20\d\d-(0[1-9]|1[0-2])_\d{6}(_\d+)?$")
LIMITE_UPLOAD = 200 * 1024 * 1024
TRAVA = threading.Lock()      # os módulos usam stdout e pastas de trabalho: uma rodada por vez


def ler_multipart(content_type: str, corpo: bytes) -> tuple[dict[str, str], list[tuple[str, bytes]]]:
    """Campos de texto e arquivos de um POST multipart/form-data (sem o módulo cgi, que saiu do Python 3.13).
    Cada parte é cortada pelos bytes do limite e guardada exatamente como chegou. O parser de e-mail só lê os cabeçalhos:
    se lesse o corpo, um .eml (que o navegador manda como message/rfc822) viraria mensagem aninhada e chegaria vazio."""
    limite = re.search(r'boundary="?([^";]+)"?', content_type or "")
    campos: dict[str, str] = {}
    arquivos: list[tuple[str, bytes]] = []
    if not limite:
        return campos, arquivos
    for bloco in corpo.split(b"--" + limite.group(1).encode("latin-1"))[1:]:
        if bloco.startswith(b"--"):            # limite final
            break
        cabecalho, separador, dados = bloco.removeprefix(b"\r\n").partition(b"\r\n\r\n")
        if not separador:
            continue
        parte = BytesParser(policy=HTTP).parsebytes(cabecalho + b"\r\n\r\n", headersonly=True)
        nome_campo = parte.get_param("name", header="content-disposition")
        arquivo = parte.get_filename()
        dados = dados.removesuffix(b"\r\n")
        if arquivo:
            arquivos.append((Path(arquivo.replace("\\", "/")).name, dados))     # só o nome, nunca o caminho
        elif nome_campo:
            campos[nome_campo] = dados.decode("utf-8", errors="replace")
    return campos, arquivos


def _nova_pasta(mes: str) -> tuple[str, Path]:
    base = f"{mes}_{datetime.now():%H%M%S}"
    id_, n = base, 1
    while (EXECUCOES / id_).exists():
        n += 1
        id_ = f"{base}_{n}"
    pasta = EXECUCOES / id_
    for sub in ("input", "data", "saida"):
        (pasta / sub).mkdir(parents=True)
    return id_, pasta


def _ler(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def executar_rodada(mes: str, origem: str, arquivos: list[tuple[str, bytes]]) -> tuple[int, dict]:
    """Roda o fechamento e devolve (status HTTP, JSON). Nunca levanta: erros viram mensagem para a tela."""
    if not re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])", mes or ""):
        return 422, {"erro": "Informe o mês no formato AAAA-MM (por exemplo 2026-09)."}
    id_, pasta = _nova_pasta(mes)
    rejeitados: list[str] = []
    if origem == "exemplo":
        for p in sorted(ENTRADA_CASE.glob("*")):
            if p.is_file() and NOME_VALIDO.match(p.name):
                shutil.copy2(p, pasta / "input" / p.name)
    else:
        for nome, dados in arquivos:
            if NOME_VALIDO.match(nome):
                (pasta / "input" / nome).write_bytes(dados)
            else:
                rejeitados.append(nome)
    enviados = sorted(p.name for p in (pasta / "input").glob("*"))
    try:
        with TRAVA:
            res = fechamento.fechar(mes, pasta / "input", pasta / "data", pasta / "saida", RAIZ / "config")
            resumo = fechamento.resumir(pasta / "saida", pasta / "data")
    except EntradaIncompleta as e:
        faltam, _ = fechamento.conferir_entrada(pasta / "input")
        return 422, {"erro": "Faltam arquivos do mês. Nada foi calculado.", "faltam": faltam, "enviados": enviados, "rejeitados": rejeitados}
    except (ValueError, FileNotFoundError) as e:
        return 422, {"erro": str(e), "enviados": enviados, "rejeitados": rejeitados}
    except Exception as e:      # defeito do código ou arquivo em formato inesperado: avisar, não quebrar sem ninguém perceber
        return 500, {"erro": f"Erro ao processar os arquivos: {type(e).__name__}: {e}", "detalhe": traceback.format_exc(limit=3)}
    resumo.update({
        "id": id_, "mes": mes, "origem": origem, "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "enviados": enviados, "rejeitados": rejeitados,
        "passos": res["passos"], "validador": res["validador"],
    })
    (pasta / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False), encoding="utf-8")
    return 200, resumo


def estado() -> dict:
    nomes = sorted(p.name for p in ENTRADA_CASE.glob("*") if p.is_file()) if ENTRADA_CASE.is_dir() else []
    return {
        "mes_sugerido": fechamento.inferir_mes(nomes),
        "arquivos_case": nomes,
        "fontes": [{"prefixo": p, "extensao": e, "nome": n} for p, e, n in FONTES],
        "saidas": [f"{n}.csv" for n in SAIDAS],
    }


def rastro_de(id_execucao: str, id_saida: str) -> dict:
    saida = EXECUCOES / id_execucao / "saida"
    linhas = [r for r in _ler(saida / "rastro.csv") if r["id_saida"] == id_saida]
    from decimal import Decimal
    soma = sum((Decimal(r["valor"]) for r in linhas), Decimal(0))
    reportado, arquivo = None, None
    for nome, coluna in (("comissoes_por_lojista", "comissao_brl"), ("notas_a_emitir", "valor_brl"), ("pendencias", "valor_brl"),
                         ("divergencias_taxa", "diferenca_brl"), ("lancamentos_classificados", "valor")):
        achado = next((r for r in _ler(saida / f"{nome}.csv") if r["id_saida"] == id_saida), None)
        if achado:
            reportado, arquivo = achado[coluna], f"{nome}.csv"
            break
    return {"id_saida": id_saida, "arquivo": arquivo, "reportado": reportado, "soma_rastro": str(soma),
            "fecha": reportado is not None and Decimal(reportado) == soma, "linhas": linhas[:1000], "total_linhas": len(linhas)}


def divergencias_de(id_execucao: str, cnpj: str, linha: str) -> list[dict]:
    return [r for r in _ler(EXECUCOES / id_execucao / "saida" / "divergencias_taxa.csv")
            if r["cnpj"] == cnpj and r["linha_negocio"] == linha]


class Servidor(BaseHTTPRequestHandler):
    server_version = "FechamentoTarvo"

    def log_message(self, *args) -> None:       # terminal limpo
        pass

    def _enviar(self, status: int, corpo: bytes, tipo: str, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, status: int, dado) -> None:
        self._enviar(status, json.dumps(dado, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        url = urlparse(self.path)
        rota, q = url.path, {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if rota in ("/", "/index.html"):
                return self._enviar(200, PAGINA.read_bytes(), "text/html; charset=utf-8")
            if rota == "/api/estado":
                return self._json(200, estado())
            if rota.startswith("/api/execucao/"):
                id_ = unquote(rota.rsplit("/", 1)[1])
                arq = EXECUCOES / id_ / "resumo.json"
                if ID_EXECUCAO.match(id_) and arq.exists():
                    return self._enviar(200, arq.read_bytes(), "application/json; charset=utf-8")
                return self._json(404, {"erro": "Execução não encontrada."})
            if rota == "/api/rastro":
                if not ID_EXECUCAO.match(q.get("e", "")) or not q.get("id"):
                    return self._json(400, {"erro": "Parâmetros inválidos."})
                return self._json(200, rastro_de(q["e"], q["id"]))
            if rota == "/api/divergencias":
                if not ID_EXECUCAO.match(q.get("e", "")):
                    return self._json(400, {"erro": "Parâmetros inválidos."})
                return self._json(200, divergencias_de(q["e"], q.get("cnpj", ""), q.get("linha", "")))
            if rota.startswith("/baixar/"):
                _, _, id_, nome = rota.split("/", 3)
                id_, nome = unquote(id_), unquote(nome)
                pasta = EXECUCOES / id_ / "saida"
                if not ID_EXECUCAO.match(id_) or not pasta.is_dir():
                    return self._json(404, {"erro": "Execução não encontrada."})
                if nome == "saidas.zip":
                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                        for n in SAIDAS:
                            z.write(pasta / f"{n}.csv", f"saida/{n}.csv")
                    return self._enviar(200, buf.getvalue(), "application/zip", {"Content-Disposition": f'attachment; filename="saida_{id_}.zip"'})
                if nome in {f"{n}.csv" for n in SAIDAS}:
                    return self._enviar(200, (pasta / nome).read_bytes(), "text/csv; charset=utf-8", {"Content-Disposition": f'attachment; filename="{nome}"'})
            return self._json(404, {"erro": "Não encontrado."})
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as e:
            return self._json(500, {"erro": f"{type(e).__name__}: {e}"})

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/fechar":
            return self._json(404, {"erro": "Não encontrado."})
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            if tamanho > LIMITE_UPLOAD:
                return self._json(413, {"erro": "Arquivos grandes demais (limite de 200 MB)."})
            campos, arquivos = ler_multipart(self.headers.get("Content-Type", ""), self.rfile.read(tamanho))
            status, corpo = executar_rodada(campos.get("mes", "").strip(), campos.get("origem", "upload"), arquivos)
            return self._json(status, corpo)
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as e:
            return self._json(500, {"erro": f"{type(e).__name__}: {e}"})


def criar_servidor(porta: int = 8765, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, porta), Servidor)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m src.app", description="Tela do fechamento Tarvo (roda neste computador).")
    ap.add_argument("--porta", type=int, default=8765)
    ap.add_argument("--sem-navegador", action="store_true", help="não abre o navegador sozinho")
    a = ap.parse_args(argv)
    try:
        srv = criar_servidor(a.porta)
    except OSError as e:
        print(f"Não consegui abrir a porta {a.porta} ({e}). Tente outra: python -m src.app --porta 9000", file=sys.stderr)
        return 1
    url = f"http://127.0.0.1:{a.porta}"
    print(f"Fechamento Tarvo: tela em {url}  (Ctrl+C para encerrar)")
    if not a.sem_navegador:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
