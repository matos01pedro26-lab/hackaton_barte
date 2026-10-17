"""Validador das saídas: formato do edital e rastro.

Uso (a partir da raiz):
    python -m src.validador --saida saida --dados data

Confere, para os seis arquivos de saida/:
  1. colunas obrigatórias, separador ';', decimal com ponto e 2 casas, data AAAA-MM-DD, CNPJ com 14 dígitos;
  2. id_saida único dentro de cada arquivo e sem repetição entre arquivos;
  3. REGRA CENTRAL: para cada id_saida, a soma de rastro.csv é igual ao número reportado, ao centavo;
     e nenhum id do rastro fica sem número reportado;
  4. pendências sempre com tipo, motivo e quem_decide;
  5. notas: sem nota para comissão ≤ 0; soma das notas de checkout = soma das comissões positivas;
     nota da remessa = soma das comissões de remessa;
  6. lançamentos: só contas que aceitam lançamento; conta vazia só com metodo HUMANO; Aurora fechando com o saldo.
Sai com código 1 se algo não fechar.
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from decimal import Decimal
from pathlib import Path

from .utils import ler_texto

OBRIGATORIAS = {
    "comissoes_por_lojista": ["id_saida", "cnpj", "lojista", "linha_negocio", "comissao_brl"],
    "divergencias_taxa": ["id_saida", "cnpj", "linha_negocio", "ref_origem", "taxa_contratada_pct", "taxa_aplicada_pct",
                          "diferenca_brl"],
    "notas_a_emitir": ["id_saida", "tomador_cnpj", "tomador", "linha_negocio", "valor_brl", "discriminacao"],
    "lancamentos_classificados": ["id_saida", "banco", "ref_origem", "data", "descricao", "valor", "conta_codigo", "metodo",
                                  "confianca"],
    "pendencias": ["id_saida", "tipo", "ref_origem", "valor_brl", "motivo", "quem_decide"],
    "rastro": ["id_saida", "arquivo_origem", "ref_origem", "valor"],
}
VALOR = {"comissoes_por_lojista": "comissao_brl", "divergencias_taxa": "diferenca_brl", "notas_a_emitir": "valor_brl",
         "lancamentos_classificados": "valor", "pendencias": "valor_brl"}
DINHEIRO = {"comissao_brl", "diferenca_brl", "valor_brl", "valor", "spread_brl", "base_brl", "valor_referencia_brl"}
DATA_OU_TEXTO = {"prazo", "data_decisao"}          # data, se for data, em AAAA-MM-DD; texto livre é permitido no prazo
DECISOR_SEM_PESSOA = {"financeiro", "comercial", "tesouraria", ""}
CNPJ = {"cnpj", "tomador_cnpj"}
RE_DINHEIRO = re.compile(r"^-?\d+\.\d{2}$")
RE_PCT = re.compile(r"^-?\d+(\.\d+)?$")
RE_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ENUMS = {"linha_negocio": {"CHECKOUT", "REMESSA"}, "banco": {"AURORA", "MERIDIANO"}, "metodo": {"REGRA", "IA", "HUMANO"}}


def D(v) -> Decimal:
    return Decimal(str(v))


def validar(saidas: dict, plano: dict | None = None) -> list[str]:
    """`saidas` mapeia o nome de cada arquivo para a lista de linhas (dicts); valores podem ser str ou Decimal.
    Devolve a lista de problemas (vazia se tudo fecha)."""
    erros: list[str] = []

    # 1. colunas e formatos
    for nome, obrig in OBRIGATORIAS.items():
        linhas = saidas.get(nome)
        if linhas is None:
            erros.append(f"{nome}: arquivo ausente")
            continue
        for i, l in enumerate(linhas, start=2):
            faltam = [c for c in obrig if c not in l]
            if faltam:
                erros.append(f"{nome} linha {i}: faltam colunas {faltam}")
                break
            for col, v in l.items():
                s = str(v)
                if col in DINHEIRO and s != "" and not RE_DINHEIRO.match(s):
                    erros.append(f"{nome} {l['id_saida']}: {col}='{s}' não é decimal com ponto e 2 casas")
                elif col in ("taxa_contratada_pct", "taxa_aplicada_pct") and not RE_PCT.match(s):
                    erros.append(f"{nome} {l['id_saida']}: {col}='{s}' fora do formato")
                elif col in CNPJ and s != "" and not re.fullmatch(r"\d{14}", s):
                    erros.append(f"{nome} {l['id_saida']}: {col}='{s}' não tem 14 dígitos")
                elif col == "data" and not RE_DATA.match(s):
                    erros.append(f"{nome} {l['id_saida']}: data='{s}' fora de AAAA-MM-DD")
                elif col in ENUMS and s not in ENUMS[col]:
                    erros.append(f"{nome} {l['id_saida']}: {col}='{s}' fora de {sorted(ENUMS[col])}")
                elif col == "confianca" and not (Decimal("0") <= D(s) <= Decimal("1")):
                    erros.append(f"{nome} {l['id_saida']}: confianca={s} fora de 0 a 1")
                elif col in DATA_OU_TEXTO and s[:1].isdigit() and not RE_DATA.match(s):
                    erros.append(f"{nome} {l['id_saida']}: {col}='{s}' fora de AAAA-MM-DD")
                elif col == "data_decisao" and s and not RE_DATA.match(s):
                    erros.append(f"{nome} {l['id_saida']}: data_decisao='{s}' fora de AAAA-MM-DD")
                elif col == "quem_decide" and s.strip().lower() in DECISOR_SEM_PESSOA:
                    erros.append(f"{nome} {l['id_saida']}: quem_decide='{s}' sem pessoa")

    # 2. ids únicos
    donos: dict[str, str] = {}
    for nome in OBRIGATORIAS:
        if nome == "rastro":                      # no rastro o mesmo id_saida aparece em várias linhas, de propósito
            continue
        vistos = set()
        for l in saidas.get(nome, []):
            i = l["id_saida"]
            if i in vistos:
                erros.append(f"{nome}: id_saida repetido {i}")
            vistos.add(i)
            if i in donos and donos[i] != nome:
                erros.append(f"id_saida {i} aparece em {donos[i]} e em {nome}")
            donos[i] = nome

    # 3. rastro: a soma por id_saida tem que bater com o número reportado
    soma: dict[str, Decimal] = {}
    for r in saidas.get("rastro", []):
        soma[r["id_saida"]] = soma.get(r["id_saida"], Decimal("0")) + D(r["valor"])
        for c in ("arquivo_origem", "ref_origem"):
            if not str(r.get(c, "")).strip():
                erros.append(f"rastro {r['id_saida']}: {c} vazio")
    for nome, col in VALOR.items():
        for l in saidas.get(nome, []):
            achado = soma.get(l["id_saida"])
            if achado is None:
                erros.append(f"{nome} {l['id_saida']}: sem rastro")
            elif achado != D(l[col]):
                erros.append(f"{nome} {l['id_saida']}: reportado={l[col]} rastro={achado}")
    erros += [f"rastro sem número reportado: {i}" for i in sorted(set(soma) - set(donos))]

    # 4. pendências
    for l in saidas.get("pendencias", []):
        for c in ("tipo", "motivo", "quem_decide"):
            if not str(l.get(c, "")).strip():
                erros.append(f"pendencias {l['id_saida']}: {c} vazio")

    # 5. notas
    comissoes, notas = saidas.get("comissoes_por_lojista", []), saidas.get("notas_a_emitir", [])
    por_cnpj = {(c["cnpj"], c["linha_negocio"]): D(c["comissao_brl"]) for c in comissoes}
    for n in notas:
        comissao = por_cnpj.get((n["tomador_cnpj"], n["linha_negocio"]))
        if n["linha_negocio"] == "CHECKOUT":
            if comissao is None:
                erros.append(f"notas {n['id_saida']}: lojista sem comissão de checkout")
            elif comissao <= 0:
                erros.append(f"notas {n['id_saida']}: nota para comissão não positiva ({comissao})")
            elif D(n["valor_brl"]) != comissao:
                erros.append(f"notas {n['id_saida']}: valor {n['valor_brl']} difere da comissão {comissao}")
    for linha in ("CHECKOUT", "REMESSA"):
        notas_l = sum((D(n["valor_brl"]) for n in notas if n["linha_negocio"] == linha), Decimal("0"))
        comissao_l = sum((D(c["comissao_brl"]) for c in comissoes if c["linha_negocio"] == linha and D(c["comissao_brl"]) > 0),
                         Decimal("0"))
        if linha == "REMESSA":
            comissao_l = sum((D(c["comissao_brl"]) for c in comissoes if c["linha_negocio"] == linha), Decimal("0"))
            if notas_l != comissao_l and comissao_l > 0:
                erros.append(f"notas REMESSA: {notas_l} difere da soma das comissões {comissao_l}")
        elif notas_l != comissao_l:
            erros.append(f"notas CHECKOUT: {notas_l} difere da soma das comissões positivas {comissao_l}")

    # 6. lançamentos
    if plano is not None:
        aceitas = {c for c, r in plano.items() if r["aceita_lancamento"] == "S"}
        for l in saidas.get("lancamentos_classificados", []):
            conta = l["conta_codigo"]
            if conta == "" and l["metodo"] != "HUMANO":
                erros.append(f"lancamentos {l['id_saida']}: conta vazia com metodo {l['metodo']}")
            elif conta != "" and conta not in aceitas:
                erros.append(f"lancamentos {l['id_saida']}: conta {conta} não aceita lançamento")
    for s in saidas.get("saldos", []):
        if s["bate"] is False:
            erros.append(f"lancamentos {s['banco']}: soma {s['soma']} não bate com o saldo do extrato")
    return erros


# ----------------------------------------------------------------------------- leitura de arquivos
def carregar(pasta: Path) -> tuple[dict, list[str]]:
    """Lê os seis arquivos como texto puro. Devolve (saidas, erros de estrutura)."""
    saidas, erros = {}, []
    for nome, obrig in OBRIGATORIAS.items():
        caminho = Path(pasta) / f"{nome}.csv"
        if not caminho.exists():
            erros.append(f"{nome}.csv ausente em {pasta}")
            continue
        texto, _ = ler_texto(caminho)
        cabecalho = texto.splitlines()[0].split(";") if texto.strip() else []
        faltam = [c for c in obrig if c not in cabecalho]
        if faltam:
            erros.append(f"{nome}.csv: cabeçalho sem {faltam} (separador ';'?)")
            continue
        linhas = []
        for r in csv.DictReader(io.StringIO(texto), delimiter=";"):
            if None in r:
                erros.append(f"{nome}.csv: linha com campos a mais ({r.get('id_saida')})")
            linhas.append({k: (v or "") for k, v in r.items() if k is not None})
        saidas[nome] = linhas
    return saidas, erros


def relatorio(saidas: dict) -> list[tuple[str, int, str]]:
    soma: dict[str, Decimal] = {}
    for r in saidas.get("rastro", []):
        soma[r["id_saida"]] = soma.get(r["id_saida"], Decimal("0")) + D(r["valor"])
    out = []
    for nome in OBRIGATORIAS:
        linhas = saidas.get(nome, [])
        if nome in VALOR:
            col = VALOR[nome]
            ok = sum(1 for l in linhas if soma.get(l["id_saida"]) == D(l[col]))
            out.append((nome, len(linhas), f"rastro fecha em {ok} de {len(linhas)} ids"))
        elif nome == "rastro":
            out.append((nome, len(linhas), f"{len(soma)} ids distintos"))
        else:
            out.append((nome, len(linhas), ""))
    return out


def main(argv: list[str] | None = None) -> int:
    from . import classificacao

    ap = argparse.ArgumentParser(description="Valida as saídas no formato do edital e o rastro.")
    ap.add_argument("--saida", default="saida")
    ap.add_argument("--dados", default="data", help="pasta com dim_plano_contas.csv e controle_ingestao.csv")
    a = ap.parse_args(argv)
    saidas, erros = carregar(Path(a.saida))
    if not erros:
        plano = classificacao.ler_plano(Path(a.dados) / "dim_plano_contas.csv")
        lc = [{"banco": l["banco"], "valor": D(l["valor"])} for l in saidas["lancamentos_classificados"]]
        saidas["saldos"] = classificacao.conferir_saldos(lc, classificacao.ler_controle(Path(a.dados) / "controle_ingestao.csv"))
        erros += validar(saidas, plano)
    for nome, n, nota in relatorio({k: v for k, v in saidas.items() if k != "saldos"}):
        print(f"  {nome + '.csv':<32}{n:>6} linhas  {nota}")
    if erros:
        print(f"\nVALIDADOR: {len(erros)} problema(s)")
        for e in erros[:40]:
            print("  -", e)
        return 1
    print("\nVALIDADOR: tudo fecha (formato, ids, rastro por id_saida, notas, contas e saldo do Aurora)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
