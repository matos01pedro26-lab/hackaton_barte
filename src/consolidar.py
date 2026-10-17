"""Consolida as saídas dos módulos no formato do edital, na raiz de saida/.

Uso (a partir da raiz, depois de ingestao, checkouts e remessa):
    python -m src.ingestao --mes 2026-09 --entrada input --saida data
    python -m src.checkouts --mes 2026-09
    python -m src.remessa --mes 2026-09
    python -m src.consolidar --mes 2026-09

Lê saida/checkouts/ e saida/parcial/ (sem alterá-las) e grava em saida/:
    comissoes_por_lojista.csv, divergencias_taxa.csv, notas_a_emitir.csv, lancamentos_classificados.csv,
    pendencias.csv, rastro.csv

O que este módulo faz que os módulos de checkout e remessa não fazem:
  * junta CHECKOUT e REMESSA em um arquivo só;
  * monta as notas de checkout (uma por lojista com comissão positiva) e junta a nota da remessa;
  * classifica os extratos (src.classificacao);
  * acrescenta as pendências dos bancos (config/pendencias_bancos.csv);
  * ajusta pendências que os módulos geram (ver ajustar_pendencias) e padroniza quem_decide.
Nenhuma regra de negócio nova: valores vêm dos módulos ou de data/, e cada número tem rastro. O resultado só é
gravado depois de passar pelo validador (src.validador).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from . import classificacao
from .utils import escrever_csv, ler_texto
from .validador import DINHEIRO, validar

CENTAVO = Decimal("0.01")

COL_COMISSOES = ["id_saida", "cnpj", "lojista", "linha_negocio", "comissao_brl"]
COL_DIVERGENCIAS = ["id_saida", "cnpj", "linha_negocio", "ref_origem", "taxa_contratada_pct", "taxa_aplicada_pct",
                    "diferenca_brl", "classe", "regra_spread", "spread_brl", "base_brl"]
COL_NOTAS = ["id_saida", "tomador_cnpj", "tomador", "linha_negocio", "valor_brl", "discriminacao"]
COL_PENDENCIAS = ["id_saida", "tipo", "ref_origem", "valor_brl", "motivo", "quem_decide",
                  "prazo", "data_decisao", "valor_referencia_brl", "base_valor"]       # as 4 últimas são extras (o edital permite)
COL_RASTRO = ["id_saida", "arquivo_origem", "ref_origem", "valor", "ref_original"]

HELENA = "Helena (financeiro)"
DIEGO = "Diego (comercial)"
BIA = "Bia (checkout)"
# quem_decide sempre com uma pessoa. Helena decide o fechamento; o comercial (Diego) decide taxa, condição e contrato;
# registrar EC ou condição na planilha de taxas é tarefa da Bia, que mantém a planilha (duvidas_financeiro.csv, 20 e 23).
QUEM_DECIDE = {"Financeiro": HELENA, "Helena/financeiro": HELENA, "Helena": HELENA,
               "Comercial": DIEGO, "comercial": DIEGO, "Comercial (Diego)": DIEGO}
QUEM_DECIDE_POR_TIPO = {"CADASTRO_EC": BIA, "CADASTRO_CONDICAO": BIA, "TAXA_A_CONFIRMAR": HELENA}
TIPOS_PONTE = ("CONTESTACAO_PONTE", "SPREAD_NEGATIVO", "CONTESTACAO_ATE_CONTRATO", "DUPLICATA", "AJUSTE_NAO_RECONHECIDO")
A_DEFINIR = "A DEFINIR (Helena)"
# De onde sai o valor_brl de cada tipo de pendência.
BASE_VALOR = {
    "EC_RETIDO": "TAXA_ORBE", "CADASTRO_EC": "COMISSAO_CONTRATADA", "CADASTRO_CONDICAO": "REFERENCIA",
    "DEVOLUCAO_CONDICAO": "TAXA_ORBE", "COMISSAO_NAO_POSITIVA": "COMISSAO_CONTRATADA",
    "CONTESTACAO_ORBE": "DIVERGENCIA_TAXA", "TAXA_A_CONFIRMAR": "DIFERENCA_DE_TAXA", "SEM_TAXA_CONTRATADA": "BRUTO",
    "EC_PENDENTE": "BRUTO", "DUPLICATA": "PARTE_TARVO_SPREAD", "SPREAD_NEGATIVO": "SPREAD_RELATORIO",
    "CONTESTACAO_ATE_CONTRATO": "DIFERENCA_ATE_CONTRATO", "CONTESTACAO_PONTE": "DIVERGENCIA_VALOR_CHEIO",
    "FORA_COMPETENCIA": "SPREAD_RELATORIO", "AJUSTE_NAO_RECONHECIDO": "SPREAD_RELATORIO",
    "CADASTRO_AUSENTE": "PARTE_TARVO_SPREAD", "NOTA_NAO_EMITIDA": "PARTICIPACAO_TARVO",
    "RAZAO_SOCIAL_NOTAS": "VALOR_DAS_NOTAS", "CONTA_GARANTIDA_SEM_ENCARGOS": "REFERENCIA",
    "LANCAMENTO_SEM_REGRA": "VALOR_EXTRATO", "PIX_SEM_IDENTIFICACAO": "VALOR_EXTRATO", "DEVOLUCAO_PIX": "VALOR_EXTRATO",
    "PIX_SEM_OPERACAO": "VALOR_EXTRATO", "TRANSFERENCIA_EM_TRANSITO": "VALOR_EXTRATO",
}


def brl(v: Decimal) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def arredondar(v: Decimal) -> Decimal:
    return v.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def ler_csv(caminho: Path) -> list[dict]:
    texto, _ = ler_texto(caminho)
    linhas = []
    for r in csv.DictReader(io.StringIO(texto), delimiter=";"):
        if None in r:
            raise ValueError(f"{caminho}: linha com campos a mais (algum texto tem ';')")
        linhas.append({k: (v or "") for k, v in r.items()})
    return linhas


def decimais(linhas: list[dict], *campos: str) -> list[dict]:
    return [{**l, **{c: Decimal(l[c]) for c in campos}} for l in linhas]


def prazo_ponte(data_email: date | None = None, dias_uteis: int = 5) -> str:
    """Prazo de contestação que o e-mail da Ponte dá (5 dias úteis a contar da data do e-mail). Feriado não é considerado.
    A data vem do próprio e-mail do mês (controle_ingestao); sem ela, só avisa que o prazo é a confirmar."""
    if data_email is None:
        return f"Prazo da contestação a confirmar com a Helena: o e-mail da Ponte dá {dias_uteis} dias úteis, contados da data dele."
    d, n = data_email, 0
    while n < dias_uteis:
        d += timedelta(days=1)
        n += d.weekday() < 5
    return (f"Prazo da contestação a confirmar com a Helena: o e-mail da Ponte de {data_email:%d/%m} dá {dias_uteis} dias "
            f"úteis (até {d:%d/%m}).")


def data_limite_ponte(data_email: date | None, dias_uteis: int = 5) -> str:
    """A mesma conta de prazo_ponte, em AAAA-MM-DD, para a coluna prazo. Sem a data do e-mail, não inventa."""
    if data_email is None:
        return A_DEFINIR
    d, n = data_email, 0
    while n < dias_uteis:
        d += timedelta(days=1)
        n += d.weekday() < 5
    return d.isoformat()


def proximo_mes(mes: str) -> str:
    ano, mm = map(int, mes.split("-"))
    return f"{ano + mm // 12}-{mm % 12 + 1:02d}"


def completar_pendencia(p: dict, mes: str, data_email: date | None) -> dict:
    """Colunas extras de pendencias.csv e quem_decide com pessoa. Prazo só com fato: a data do e-mail da Ponte e o
    fechamento seguinte para a Atlas (duvidas_financeiro.csv, 16); o resto fica a definir pela Helena."""
    p = dict(p)
    p["quem_decide"] = QUEM_DECIDE_POR_TIPO.get(p["tipo"], QUEM_DECIDE.get(p["quem_decide"], p["quem_decide"]))
    if p["tipo"] in TIPOS_PONTE:
        p.setdefault("prazo", data_limite_ponte(data_email))
    elif p["tipo"] == "EC_RETIDO":
        p.setdefault("prazo", f"fechamento de {proximo_mes(mes)}")
    p.setdefault("prazo", A_DEFINIR)
    p.setdefault("data_decisao", "")
    p.setdefault("valor_referencia_brl", "")
    p.setdefault("base_valor", BASE_VALOR.get(p["tipo"], ""))
    return p


# ----------------------------------------------------------------------------- notas de checkout
def notas_checkout(comissoes: list[dict], pendencias: list[dict], rastro: list[dict], mes: str) -> tuple[list[dict], list[dict]]:
    """Uma nota por lojista de checkout com comissão positiva. Zero ou negativo não emite (regra da Helena)."""
    ano, mm = mes.split("-")
    por_id: dict[str, list[dict]] = {}
    for r in rastro:
        por_id.setdefault(r["id_saida"], []).append(r)
    notas, rastro_notas = [], []
    for c in sorted(comissoes, key=lambda c: c["cnpj"]):
        if c["linha_negocio"] != "CHECKOUT" or c["comissao_brl"] <= 0:
            continue
        id_nota = f"NF-CHK-{mes}-{c['cnpj']}"
        texto = f"Taxa de processamento de pagamentos (MDR) e de antecipação, competência {mm}/{ano}."
        notas.append({"id_saida": id_nota, "tomador_cnpj": c["cnpj"], "tomador": c["lojista"],
                      "linha_negocio": "CHECKOUT", "valor_brl": c["comissao_brl"], "discriminacao": texto})
        rastro_notas += [{**r, "id_saida": id_nota, "ref_original": r.get("ref_original", "")} for r in por_id[c["id_saida"]]]
    return notas, rastro_notas


def pendencia_razao_social(notas: list[dict], linha_planilha: dict[str, str], mes: str) -> tuple[list[dict], list[dict]]:
    """A nota de checkout usa como tomador o nome da planilha de taxas. A razão social oficial não está no pacote, então a
    conferência vira uma pendência só (valor = soma das notas), com uma linha de rastro por nota apontando para a linha
    da planilha de onde saiu o nome."""
    chk = [n for n in notas if n["linha_negocio"] == "CHECKOUT"]
    if not chk:
        return [], []
    id_saida = f"PEN-CHK-{mes}-RAZAO_SOCIAL_NOTAS"
    total = sum((n["valor_brl"] for n in chk), Decimal("0.00"))
    pend = {"id_saida": id_saida, "tipo": "RAZAO_SOCIAL_NOTAS", "ref_origem": "|".join(n["id_saida"] for n in chk),
            "valor_brl": total,
            "motivo": (f"As {len(chk)} notas de checkout usam como tomador o nome da planilha de taxas, com o CNPJ. A razão "
                       "social oficial não está no pacote de dados. A Helena aceitou o nome da planilha com o CNPJ e disse que a "
                       "Bia confere na emissão (duvidas_financeiro.csv, resposta 39, item 4); a pendência só fecha com "
                       "confirmação humana. valor_brl = soma das notas afetadas."),
            "quem_decide": HELENA}
    rastro = [{"id_saida": id_saida, "arquivo_origem": "02_tabela_taxas_contratadas.xlsx",
               "ref_origem": "linha " + linha_planilha.get(n["tomador_cnpj"], "?").replace(" | ", "|"),
               "valor": n["valor_brl"], "ref_original": n["id_saida"]} for n in chk]
    return [pend], rastro


# ----------------------------------------------------------------------------- ajustes nas pendências dos módulos
def _trocar_rastro(rastro: list[dict], id_saida: str, novas: list[dict]) -> list[dict]:
    return [r for r in rastro if r["id_saida"] != id_saida] + novas


def ajustar_pendencias(pendencias: list[dict], rastro: list[dict], fato_orbe: dict[str, dict],
                       participacao_tarvo: Decimal, data_email: date | None = None) -> tuple[list[dict], list[dict], list[str]]:
    """Correções pedidas na consolidação. Devolve (pendências, rastro, avisos do que foi feito)."""
    avisos: list[str] = []
    por_tipo = {}
    for p in pendencias:
        por_tipo.setdefault(p["tipo"], []).append(p)
    devolucao = next((p for p in por_tipo.get("DEVOLUCAO_CONDICAO", [])), None)
    saida: list[dict] = []
    for p in pendencias:
        p = dict(p)
        linhas = [r for r in rastro if r["id_saida"] == p["id_saida"]]
        if p["tipo"] == "CADASTRO_CONDICAO" and devolucao is not None:
            # Mesmas transações da devolução: fica como referência, sem somar.
            original = p["valor_brl"]
            p["motivo"] = (f"REFERÊNCIA, NÃO SOMAR: cobre as mesmas {len(linhas)} transações da devolução {devolucao['id_saida']} "
                           f"(R$ {brl(devolucao['valor_brl'])}). Valor que a planilha cobraria (bruto x taxa), só para consulta: "
                           f"R$ {brl(original)}. " + p["motivo"])
            p["valor_brl"] = Decimal("0.00")
            p["valor_referencia_brl"] = original
            rastro = _trocar_rastro(rastro, p["id_saida"], [{**r, "valor": Decimal("0.00")} for r in linhas])
            avisos.append(f"{p['id_saida']}: valor {original} -> 0.00 (referência da devolução)")
        elif p["tipo"] == "DUPLICATA":
            total = p["valor_brl"]
            p["valor_brl"] = arredondar(total * participacao_tarvo)
            p["motivo"] += (f" valor_brl = parte da Tarvo ({participacao_tarvo * 100:.0f}%); spread total da operação repetida: "
                            f"R$ {brl(total)}.")
            rastro = _trocar_rastro(rastro, p["id_saida"], [{**r, "valor": p["valor_brl"]} for r in linhas])
            avisos.append(f"{p['id_saida']}: valor {total} -> {p['valor_brl']}")
        elif p["tipo"] == "CONTESTACAO_ATE_CONTRATO":
            original = p["valor_brl"]
            p["valor_brl"] = abs(original)
            p["motivo"] = "A PEDIR À PONTE (valor positivo = quanto a Tarvo pede). " + p["motivo"]
            rastro = _trocar_rastro(rastro, p["id_saida"], [{**r, "valor": abs(r["valor"])} for r in linhas])
            avisos.append(f"{p['id_saida']}: valor {original} -> {p['valor_brl']}")
        elif p["tipo"] == "EC_RETIDO":
            ids = [r["ref_origem"] for r in linhas]
            taxa = [fato_orbe[i] for i in ids]
            bruto = sum((Decimal(t["valor_bruto"]) for t in taxa), Decimal("0.00"))
            estimada = sum((Decimal(t["valor_taxa"]) for t in taxa), Decimal("0.00"))
            p["valor_brl"] = estimada
            p["motivo"] = p["motivo"].replace("valor = soma do bruto.", "").rstrip() + (
                f" valor_brl = taxa estimada, soma do valor_taxa cobrado pela Orbe nas {len(ids)} transações; "
                f"bruto das transações: R$ {brl(bruto)}.")
            rastro = _trocar_rastro(rastro, p["id_saida"],
                                    [{**r, "valor": Decimal(fato_orbe[r["ref_origem"]]["valor_taxa"])} for r in linhas])
            avisos.append(f"{p['id_saida']}: valor {bruto} (bruto) -> {estimada} (taxa estimada)")
        elif p["tipo"] == "CONTESTACAO_PONTE":
            p["motivo"] = "A PEDIR À PONTE (valor cheio pago a mais pelo lojista). " + p["motivo"]
        elif p["tipo"] == "SPREAD_NEGATIVO":
            p["motivo"] = ("VALOR DO RELATÓRIO (o que aconteceu; não é o valor a pedir, que está na CONTESTACAO_ATE_CONTRATO "
                           "da mesma operação). " + p["motivo"])
        if p["tipo"] in TIPOS_PONTE:
            p["motivo"] += " " + prazo_ponte(data_email)
        saida.append(p)
    return saida, rastro, avisos


# ----------------------------------------------------------------------------- pendências dos bancos
def pendencias_bancos(config: list[dict], fato_banco: list[dict], mes: str) -> tuple[list[dict], list[dict]]:
    por_ref = {(l["banco"], l["ref_origem"]): l for l in fato_banco}
    aurora = [l for l in fato_banco if l["banco"] == "AURORA"]
    por_dia: dict[str, Decimal] = {}
    for l in aurora:
        por_dia[l["data"]] = Decimal(l["saldo"])                    # saldo do fim do dia (última linha do dia)
    menor = min(aurora, key=lambda l: Decimal(l["saldo"]))
    pendencias, rastro = [], []
    for c in config:
        if c.get("mes") and c["mes"] != mes:      # pendência escrita para uma linha de outro mês: não vale neste
            continue
        ref, banco = c["ref_origem"], c["banco"]
        referencia = ""
        if ref == "@MENOR_SALDO":
            # O saldo não é dinheiro a lançar: vai como referência, e a pendência não soma nada.
            linha, valor, referencia = menor, Decimal("0.00"), Decimal(menor["saldo"])
            motivo = "REFERÊNCIA, NÃO SOMAR: " + c["motivo"].format(
                dias_negativos=sum(1 for v in por_dia.values() if v < 0),
                dias_com_lancamento=len(por_dia), data_menor_saldo=menor["data"])
            ref = menor["ref_origem"]
        else:
            if (banco, ref) not in por_ref:
                raise ValueError(f"config/pendencias_bancos.csv: {banco} {ref} não existe em fato_banco (arquivo mudou?)")
            linha, valor = por_ref[(banco, ref)], Decimal(por_ref[(banco, ref)]["valor"])
            motivo = c["motivo"].format(valor_fmt=brl(abs(valor)))
        id_saida = f"PEN-BCO-{mes}-{c['tipo']}-{ref}"
        pend = {"id_saida": id_saida, "tipo": c["tipo"], "ref_origem": ref, "valor_brl": valor,
                "motivo": motivo, "quem_decide": c["quem_decide"]}
        if referencia != "":
            pend["valor_referencia_brl"] = referencia
        pendencias.append(pend)
        rastro.append({"id_saida": id_saida, "arquivo_origem": linha["arquivo_origem"], "ref_origem": ref, "valor": valor,
                       "ref_original": ""})
    return pendencias, rastro


def lancamentos_com_decisor_pendente(config: list[dict], mes: str) -> set[tuple[str, str]]:
    """(banco, ref_origem) dos lançamentos sobre os quais há pendência aberta em config/pendencias_bancos.csv.
    @MENOR_SALDO fica de fora: a linha do menor saldo só marca o dia; a classificação dela não está em dúvida."""
    return {(c["banco"], c["ref_origem"]) for c in config
            if (not c.get("mes") or c["mes"] == mes) and c["ref_origem"] != "@MENOR_SALDO"}


def pendencias_sem_regra(sem_regra: list[dict], mes: str) -> tuple[list[dict], list[dict]]:
    pend, rast = [], []
    for l in sem_regra:
        id_saida = f"PEN-BCO-{mes}-LANCAMENTO_SEM_REGRA-{l['ref_origem']}"
        valor = Decimal(l["valor"])
        pend.append({"id_saida": id_saida, "tipo": "LANCAMENTO_SEM_REGRA", "ref_origem": l["ref_origem"], "valor_brl": valor,
                     "motivo": f"Nenhuma regra de classificação casou com '{l['descricao']}' ({l['banco']}): classificar à mão.",
                     "quem_decide": HELENA})
        rast.append({"id_saida": id_saida, "arquivo_origem": l["arquivo_origem"], "ref_origem": l["ref_origem"], "valor": valor,
                     "ref_original": ""})
    return pend, rast


# ----------------------------------------------------------------------------- execução
def executar(mes: str, dados: Path, checkout: Path, parcial: Path, config: Path, saida: Path,
             gravar: bool = True) -> dict:
    dados, checkout, parcial, config, saida = map(Path, (dados, checkout, parcial, config, saida))
    # --- entradas dos módulos
    chk_com = decimais(ler_csv(checkout / "comissoes_por_lojista.csv"), "comissao_brl")
    chk_div = decimais(ler_csv(checkout / "divergencias_taxa.csv"), "diferenca_brl")
    chk_pen = decimais(ler_csv(checkout / "pendencias.csv"), "valor_brl")
    chk_ras = decimais(ler_csv(checkout / "rastro.csv"), "valor")
    rem_com = decimais(ler_csv(parcial / "remessa_comissoes.csv"), "comissao_brl")
    rem_div = decimais(ler_csv(parcial / "remessa_divergencias.csv"), "diferenca_brl")
    rem_pen = decimais(ler_csv(parcial / "remessa_pendencias.csv"), "valor_brl")
    rem_not = decimais(ler_csv(parcial / "remessa_notas.csv"), "valor_brl")
    rem_ras = decimais(ler_csv(parcial / "remessa_rastro.csv"), "valor")
    fato_orbe = {l["id_transacao"]: l for l in ler_csv(dados / "fato_orbe.csv")}
    fato_banco = [l for l in ler_csv(dados / "fato_banco.csv") if l["competencia"] == mes]
    participacao = Decimal(json.loads((config / "remessa.json").read_text(encoding="utf-8"))["participacao_tarvo"])

    comissoes = [{k: c[k] for k in COL_COMISSOES} for c in chk_com + rem_com]
    divergencias = chk_div + rem_div
    rastro = [{**r, "ref_original": r.get("ref_original", "")} for r in chk_ras + rem_ras]

    # --- pendências dos módulos, com as correções pedidas
    controle = classificacao.ler_controle(dados / "controle_ingestao.csv")
    data_email = next((date.fromisoformat(c["valor"]) for c in controle if c["fonte"] == "ponte" and c["item"] == "data_email"), None)
    pendencias, rastro, avisos = ajustar_pendencias(chk_pen + rem_pen, rastro, fato_orbe, participacao, data_email)

    # --- notas (e a conferência da razão social do tomador, que vira pendência e não texto da nota)
    notas_chk, rastro_notas = notas_checkout(chk_com, pendencias, rastro, mes)
    notas = notas_chk + rem_not
    linha_planilha = {l["cnpj"]: l["linha_planilha"] for l in ler_csv(dados / "dim_lojista.csv")}
    pen_rs, ras_rs = pendencia_razao_social(notas_chk, linha_planilha, mes)

    # --- pendências dos bancos e classificação dos extratos (lançamento com decisor pendente tem confiança limitada)
    cfg_bancos = ler_csv(config / "pendencias_bancos.csv")
    pen_bco, ras_bco = pendencias_bancos(cfg_bancos, fato_banco, mes)
    plano = classificacao.ler_plano(dados / "dim_plano_contas.csv")
    linhas_lc, rastro_lc, sem_regra = classificacao.classificar(
        fato_banco, plano, decisor_pendente=lancamentos_com_decisor_pendente(cfg_bancos, mes))
    pen_sr, ras_sr = pendencias_sem_regra(sem_regra, mes)
    pendencias = [completar_pendencia(p, mes, data_email) for p in pendencias + pen_rs + pen_bco + pen_sr]
    rastro += rastro_notas + ras_rs + [{**r, "ref_original": ""} for r in rastro_lc] + ras_bco + ras_sr

    def ordenar(linhas: list[dict]) -> list[dict]:
        return sorted(linhas, key=lambda l: l["id_saida"])

    resultado = {
        "comissoes_por_lojista": ordenar(comissoes), "divergencias_taxa": ordenar(divergencias),
        "notas_a_emitir": ordenar(notas), "lancamentos_classificados": linhas_lc,
        "pendencias": ordenar(pendencias), "rastro": sorted(rastro, key=lambda r: (r["id_saida"], r["ref_origem"])),
        "avisos": avisos, "saldos": classificacao.conferir_saldos(linhas_lc, classificacao.ler_controle(dados / "controle_ingestao.csv")),
    }
    for nome in ("comissoes_por_lojista", "divergencias_taxa", "notas_a_emitir", "lancamentos_classificados", "pendencias", "rastro"):
        for l in resultado[nome]:
            for campo in DINHEIRO:
                if campo in l and l[campo] != "":
                    l[campo] = arredondar(Decimal(str(l[campo])))        # só formata: valores já estão em centavos
    problemas = validar(resultado, plano=plano)
    if problemas:
        raise ValueError("Saída não passou no validador:\n  " + "\n  ".join(problemas))
    if gravar:
        saida.mkdir(parents=True, exist_ok=True)
        escrever_csv(saida / "comissoes_por_lojista.csv", resultado["comissoes_por_lojista"], COL_COMISSOES)
        escrever_csv(saida / "divergencias_taxa.csv", resultado["divergencias_taxa"], COL_DIVERGENCIAS)
        escrever_csv(saida / "notas_a_emitir.csv", resultado["notas_a_emitir"], COL_NOTAS)
        escrever_csv(saida / "lancamentos_classificados.csv", resultado["lancamentos_classificados"],
                     classificacao.COL_LANCAMENTOS)
        escrever_csv(saida / "pendencias.csv", resultado["pendencias"], COL_PENDENCIAS)
        escrever_csv(saida / "rastro.csv", resultado["rastro"], COL_RASTRO)
    return resultado


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Consolida as saídas no formato do edital.")
    ap.add_argument("--mes", required=True)
    ap.add_argument("--dados", default="data")
    ap.add_argument("--checkout", default="saida/checkouts")
    ap.add_argument("--parcial", default="saida/parcial")
    ap.add_argument("--config", default="config")
    ap.add_argument("--saida", default="saida")
    a = ap.parse_args(argv)
    r = executar(a.mes, a.dados, a.checkout, a.parcial, a.config, a.saida)
    for nome in ("comissoes_por_lojista", "divergencias_taxa", "notas_a_emitir", "lancamentos_classificados", "pendencias", "rastro"):
        print(f"  {nome + '.csv':<32}{len(r[nome]):>6} linhas")
    for av in r["avisos"]:
        print("  ajuste:", av)
    return 0


if __name__ == "__main__":
    sys.exit(main())
