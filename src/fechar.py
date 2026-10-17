"""Fecha o mês com um comando: ingestão, checkout, remessa, consolidação e validador, e mostra o resultado.

Uso (a partir da raiz do repositório):
    python -m src.fechar --mes 2026-09                       # lê input/, grava data/ e saida/
    python -m src.fechar --mes 2026-10 --entrada /caminho/dos/arquivos-do-mes

O mês é sempre informado: nada no código está fixo em um mês. Os arquivos do mês ficam todos na pasta de entrada.
Não usa chave de API e nenhuma etapa chama IA: as regras vêm do financeiro (config/ e HIPOTESES.md).
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import re
import sys
import time
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from . import consolidar, ingestao, validador
from .checkouts import __main__ as checkouts_cli
from .remessa import pipeline as remessa_pipeline
from .utils import MESES

RAIZ = Path(__file__).resolve().parents[1]   # raiz do repositório: os caminhos padrão não dependem de onde o comando é rodado

# Fontes obrigatórias do mês: prefixo do nome e extensão. Os ajustes tardios da Orbe (06_*) são opcionais.
FONTES = [
    ("01_orbe", ".csv", "relatório da Orbe"),
    ("02_tabela_taxas", ".xlsx", "tabela de taxas contratadas"),
    ("03_email_ponte", ".eml", "e-mail da Ponte Câmbio"),
    ("04_plano_de_contas", ".csv", "plano de contas"),
    ("05a_extrato_banco_aurora", ".csv", "extrato do Aurora"),
    ("05b_extrato_banco_meridiano", ".ofx", "extrato do Meridiano"),
]
SAIDAS = ["comissoes_por_lojista", "divergencias_taxa", "notas_a_emitir", "lancamentos_classificados", "pendencias", "rastro"]


class EntradaIncompleta(Exception):
    """Falta ao menos uma fonte obrigatória do mês."""


def brl(v) -> str:
    """Decimal -> 'R$ 1.234,56' (formato de leitura; os arquivos continuam com ponto decimal)."""
    d = Decimal(str(v)).quantize(Decimal("0.01"))
    texto = f"{abs(d):,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return f"{'-' if d < 0 else ''}R$ {texto}"


def inferir_mes(nomes: list[str]) -> str | None:
    """'..._set2026.csv' -> '2026-09'. Devolve o mês que mais aparece nos nomes, ou None."""
    achados: dict[str, int] = defaultdict(int)
    for n in nomes:
        for m in re.finditer(r"(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)(20\d\d)", n.lower()):
            achados[f"{m.group(2)}-{MESES.index(m.group(1)) + 1:02d}"] += 1
    return max(achados, key=achados.get) if achados else None


def conferir_entrada(entrada: Path) -> tuple[list[str], list[str]]:
    """(fontes que faltam, arquivos presentes). A ingestão exige as seis fontes; não fecha só com parte delas."""
    entrada = Path(entrada)
    presentes = sorted(p.name for p in entrada.glob("*") if p.is_file()) if entrada.is_dir() else []
    faltam = [f"{prefixo}*{ext}  ({nome})" for prefixo, ext, nome in FONTES
              if not any(n.startswith(prefixo) and n.endswith(ext) for n in presentes)]
    return faltam, presentes


def _capturar(funcao, *args, **kwargs):
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        resultado = funcao(*args, **kwargs)
    return resultado, saida.getvalue()


def fechar(mes: str, entrada: Path, dados: Path, saida: Path, config: Path) -> dict:
    """Roda as cinco etapas em sequência. Devolve {'passos': [...], 'validador': {'ok', 'texto'}, 'saida': Path}.
    Levanta EntradaIncompleta se faltar fonte; ValueError se a saída não passar no validador."""
    entrada, dados, saida, config = map(Path, (entrada, dados, saida, config))
    if not re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])", mes):
        raise ValueError(f"Mês inválido: {mes!r} (use AAAA-MM, por exemplo 2026-09)")
    faltam, _ = conferir_entrada(entrada)
    if faltam:
        raise EntradaIncompleta("Faltam arquivos do mês em " + str(entrada) + ":\n  - " + "\n  - ".join(faltam))

    passos = []

    def etapa(nome, funcao, *args, **kwargs):
        t0 = time.perf_counter()
        resultado, texto = _capturar(funcao, *args, **kwargs)
        passos.append({"nome": nome, "segundos": round(time.perf_counter() - t0, 2), "log": texto.strip()})
        return resultado

    etapa("Ingestão dos arquivos", ingestao.executar, mes, entrada, dados)
    etapa("Comissão de checkout", checkouts_cli.executar, mes, dados, config, saida / "checkouts")
    etapa("Comissão de remessa", remessa_pipeline.executar, mes, dados, saida / "parcial", config / "remessa.json")
    etapa("Consolidação (seis arquivos)", consolidar.executar, mes, dados, saida / "checkouts", saida / "parcial", config, saida)
    codigo, texto = _capturar(validador.main, ["--saida", str(saida), "--dados", str(dados)])
    passos.append({"nome": "Validador do rastro", "segundos": 0.0, "log": texto.strip()})
    return {"passos": passos, "saida": saida, "validador": {"ok": codigo == 0, "texto": texto.strip()}}


# ----------------------------------------------------------------------------- leitura do resultado
def _csv(caminho: Path) -> list[dict]:
    with Path(caminho).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def resumir(saida: Path, dados: Path) -> dict:
    """Números e tabelas do fechamento, lidos dos seis arquivos finais (é o que a tela e o terminal mostram)."""
    saida, dados = Path(saida), Path(dados)
    r = {n: _csv(saida / f"{n}.csv") for n in SAIDAS}
    plano = {l["cod_conta"]: l["descricao"] for l in _csv(dados / "dim_plano_contas.csv")} if (dados / "dim_plano_contas.csv").exists() else {}
    D = Decimal

    comissao_por_linha: dict[str, Decimal] = defaultdict(Decimal)
    for c in r["comissoes_por_lojista"]:
        comissao_por_linha[c["linha_negocio"]] += D(c["comissao_brl"])
    nome_por_cnpj = {c["cnpj"]: c["lojista"] for c in r["comissoes_por_lojista"]}

    div_por: dict[tuple, list] = defaultdict(lambda: [0, D(0)])
    for d in r["divergencias_taxa"]:
        k = (d["cnpj"], d["linha_negocio"]); div_por[k][0] += 1; div_por[k][1] += D(d["diferenca_brl"])
    divergencias_por_lojista = sorted(
        ({"cnpj": c, "lojista": nome_por_cnpj.get(c, c), "linha_negocio": ln, "qtd": q, "valor": str(v)}
         for (c, ln), (q, v) in div_por.items()), key=lambda x: -abs(D(x["valor"])))

    pend: dict[str, list] = defaultdict(lambda: [0, D(0), set()])
    for p in r["pendencias"]:
        pend[p["tipo"]][0] += 1; pend[p["tipo"]][1] += D(p["valor_brl"]); pend[p["tipo"]][2].add(p["quem_decide"])
    pendencias_por_tipo = sorted(({"tipo": t, "qtd": q, "valor": str(v), "quem_decide": " / ".join(sorted(s))}
                                  for t, (q, v, s) in pend.items()), key=lambda x: -abs(D(x["valor"])))

    contas: dict[str, list] = defaultdict(lambda: [0, D(0)])
    for l in r["lancamentos_classificados"]:
        contas[l["conta_codigo"]][0] += 1; contas[l["conta_codigo"]][1] += D(l["valor"])
    lancamentos_por_conta = sorted(({"conta": c, "descricao": plano.get(c, ""), "qtd": q, "valor": str(v)}
                                    for c, (q, v) in contas.items()), key=lambda x: -x["qtd"])

    metodos: dict[str, int] = defaultdict(int)
    for l in r["lancamentos_classificados"]:
        metodos[l["metodo"]] += 1

    return {
        "kpis": {
            "comissao_total": str(sum(comissao_por_linha.values(), D(0))),
            "comissao_checkout": str(comissao_por_linha.get("CHECKOUT", D(0))),
            "comissao_remessa": str(comissao_por_linha.get("REMESSA", D(0))),
            "lojistas": len(nome_por_cnpj),
            "divergencias_qtd": len(r["divergencias_taxa"]),
            "divergencias": {ln: {"qtd": sum(1 for d in r["divergencias_taxa"] if d["linha_negocio"] == ln),
                                  "valor": str(sum((D(d["diferenca_brl"]) for d in r["divergencias_taxa"] if d["linha_negocio"] == ln), D(0)))}
                             for ln in ("CHECKOUT", "REMESSA")},
            "notas_qtd": len(r["notas_a_emitir"]),
            "notas_valor": str(sum((D(n["valor_brl"]) for n in r["notas_a_emitir"]), D(0))),
            "lancamentos_qtd": len(r["lancamentos_classificados"]),
            "pendencias_qtd": len(r["pendencias"]),
            "rastro_linhas": len(r["rastro"]),
        },
        "comissoes": r["comissoes_por_lojista"],
        "divergencias_por_lojista": divergencias_por_lojista,
        "notas": r["notas_a_emitir"],
        "pendencias": r["pendencias"],
        "pendencias_por_tipo": pendencias_por_tipo,
        "lancamentos_por_conta": lancamentos_por_conta,
        "lancamentos_por_metodo": dict(metodos),
        "arquivos": [{"nome": f"{n}.csv", "linhas": len(r[n])} for n in SAIDAS],
    }


def imprimir_resumo(res: dict, mes: str, saida: Path) -> None:
    k = res["kpis"]
    print(f"\nFechamento {mes}")
    print(f"  Comissão total ............ {brl(k['comissao_total'])}   (checkout {brl(k['comissao_checkout'])} + remessa {brl(k['comissao_remessa'])}, {k['lojistas']} lojistas)")
    print(f"  Notas a emitir ............ {k['notas_qtd']}   ({brl(k['notas_valor'])})")
    dv = k["divergencias"]
    print(f"  Divergências de taxa ...... {k['divergencias_qtd']}   (checkout {dv['CHECKOUT']['qtd']}: {brl(dv['CHECKOUT']['valor'])}; remessa {dv['REMESSA']['qtd']}: {brl(dv['REMESSA']['valor'])})")
    print(f"  Lançamentos classificados . {k['lancamentos_qtd']}   (por regra: {res['lancamentos_por_metodo'].get('REGRA', 0)})")
    print(f"  Pendências para uma pessoa  {k['pendencias_qtd']}")
    print(f"  Rastro .................... {k['rastro_linhas']} linhas")
    print("\n  Maiores pendências:")
    for p in res["pendencias_por_tipo"][:5]:
        print(f"    {p['tipo']:<30}{p['qtd']:>3}  {brl(p['valor']):>20}   decide: {p['quem_decide']}")
    print(f"\n  Seis arquivos em {Path(saida).resolve()}")


def main(argv: list[str] | None = None) -> int:
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(prog="python -m src.fechar", description="Fecha o mês: ingestão, checkout, remessa, consolidação e validador.")
    ap.add_argument("--mes", required=True, help="competência AAAA-MM (obrigatória: nada é fixo em um mês)")
    ap.add_argument("--entrada", default=str(RAIZ / "input"), help="pasta com os arquivos do mês")
    ap.add_argument("--dados", default=str(RAIZ / "data"), help="pasta das tabelas padronizadas")
    ap.add_argument("--saida", default=str(RAIZ / "saida"), help="pasta dos seis arquivos finais")
    ap.add_argument("--config", default=str(RAIZ / "config"), help="pasta com as regras como dado")
    a = ap.parse_args(argv)
    try:
        res = fechar(a.mes, Path(a.entrada), Path(a.dados), Path(a.saida), Path(a.config))
    except EntradaIncompleta as e:
        print(f"NÃO FECHOU: {e}", file=sys.stderr)
        return 2
    except (ValueError, FileNotFoundError) as e:
        print(f"NÃO FECHOU: {e}", file=sys.stderr)
        return 1
    for p in res["passos"]:
        print(f"  [ok] {p['nome']:<32}{p['segundos']:>6.2f} s")
    print("\n" + res["validador"]["texto"])
    if not res["validador"]["ok"]:
        return 1
    imprimir_resumo(resumir(a.saida, a.dados), a.mes, Path(a.saida))
    return 0


if __name__ == "__main__":
    sys.exit(main())
