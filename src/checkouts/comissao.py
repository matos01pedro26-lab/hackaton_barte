"""Comissão de checkout por lojista, com rastro até cada transação da Orbe e as pendências que exigem uma pessoa."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

from .regras import (SemTaxa, comissao_linha, condicao_vigente, data_da_taxa, divergencia_linha, taxa_contratada,
                     taxa_planilha)

LINHA_NEGOCIO = "CHECKOUT"
ZERO = Decimal("0")

# Quem decide sobre um EC fora do faturamento, pelo status em dim_ec
QUEM_DECIDE_EC = {"RETIDO": "Comercial", "PENDENTE": "Financeiro"}


@dataclass
class Entrada:
    """Linhas das tabelas de data/ (fato_orbe, dim_contrato_taxa, dim_lojista, dim_ec) e de config/."""
    competencia: str
    transacoes: list[dict]
    contratos: list[dict]
    lojistas: list[dict]
    ecs: list[dict]
    mapeamento: list[dict] = field(default_factory=list)
    condicoes: list[dict] = field(default_factory=list)
    taxas_a_confirmar: list[dict] = field(default_factory=list)


@dataclass
class Resultado:
    comissoes: list[dict]
    rastro: list[dict]
    pendencias: list[dict]
    divergencias: list[dict] = field(default_factory=list)


def id_comissao(competencia: str, cnpj: str) -> str:
    return f"CHK-{competencia}-{cnpj}"


def id_divergencia(competencia: str, id_transacao: str) -> str:
    return f"DIV-CHK-{competencia}-{id_transacao}"


def id_pendencia(competencia: str, tipo: str, chave: str) -> str:
    return f"PEN-CHK-{competencia}-{tipo}-{chave.replace('/', '-')}"


def calcular(entrada: Entrada) -> Resultado:
    comp = entrada.competencia
    nomes = {l["cnpj"]: l["nome_canonico"] for l in entrada.lojistas}
    ecs = {e["ec"]: e for e in entrada.ecs}
    total: dict[str, Decimal] = defaultdict(Decimal)
    fora: dict[str, list[dict]] = defaultdict(list)          # EC não confirmado -> transações
    por_ec: dict[str, list[tuple]] = defaultdict(list)       # EC -> (transação, comissão)
    por_condicao: dict[tuple, list[tuple]] = defaultdict(list)  # condição -> (transação, comissão dispensada)
    cobrado_a_mais: dict[str, list[tuple]] = defaultdict(list)  # CNPJ -> (transação, diferença)
    cobrado_na_concessao: dict[tuple, list[tuple]] = defaultdict(list)  # condição -> (transação, valor_taxa da Orbe)
    sob_suspeita = {(x["cnpj"], x["faixa"]): Decimal(x["taxa_referencia_pct"]) for x in entrada.taxas_a_confirmar}
    a_confirmar: dict[tuple, list[tuple]] = defaultdict(list)  # (CNPJ, faixa) -> (transação, comissão a mais)
    rastro, pendencias, divergencias = [], [], []

    def pendencia(tipo, chave, valor, motivo, quem, linhas):
        # ref_origem = as transações de origem, separadas por "|" (mesmo padrão das pendências da remessa)
        id_saida = id_pendencia(comp, tipo, chave)
        rastro.extend(_rastro(id_saida, t, v) for t, v in linhas)
        pendencias.append({"id_saida": id_saida, "tipo": tipo,
                           "ref_origem": "|".join(sorted({t["id_transacao"] for t, _ in linhas})),
                           "valor_brl": valor, "motivo": motivo, "quem_decide": quem})

    for t in sorted(entrada.transacoes, key=lambda x: x["id_transacao"]):
        bruto = Decimal(t["valor_bruto"])
        if t["status_ec"] != "CONFIRMADO":
            fora[t["ec"]].append(t)
            continue
        dia = data_da_taxa(t)
        try:
            taxa = taxa_contratada(t["cnpj"], t["faixa"], dia, entrada.contratos, entrada.condicoes)
            cond = condicao_vigente(t["cnpj"], t["faixa"], dia, entrada.condicoes)
        except SemTaxa as e:
            pendencia("SEM_TAXA_CONTRATADA", t["id_transacao"], bruto,
                      f"{e}. Transação fora da comissão; valor = bruto.", "Financeiro", [(t, bruto)])
            continue
        valor = comissao_linha(bruto, taxa)
        aplicada = Decimal(t["taxa_aplicada_pct"])
        if cond:
            # R28/R29: concessão do comercial fora do contrato não é divergência; a Tarvo devolve o que a Orbe cobrou
            if Decimal(t["valor_taxa"]):
                cobrado_na_concessao[(cond["cnpj"], cond["faixa"])].append((t, Decimal(t["valor_taxa"])))
        elif aplicada != taxa:
            diferenca = divergencia_linha(bruto, aplicada, taxa)
            id_div = id_divergencia(comp, t["id_transacao"])
            divergencias.append({"id_saida": id_div, "cnpj": t["cnpj"], "linha_negocio": LINHA_NEGOCIO,
                                 "ref_origem": t["id_transacao"], "taxa_contratada_pct": taxa,
                                 "taxa_aplicada_pct": aplicada, "diferenca_brl": diferenca})
            rastro.append(_rastro(id_div, t, diferenca))
            cobrado_a_mais[t["cnpj"]].append((t, diferenca))
        total[t["cnpj"]] += valor
        rastro.append(_rastro(id_comissao(comp, t["cnpj"]), t, valor))
        por_ec[t["ec"]].append((t, valor))
        if (t["cnpj"], t["faixa"]) in sob_suspeita:
            referencia = sob_suspeita[(t["cnpj"], t["faixa"])]
            a_confirmar[(t["cnpj"], t["faixa"])].append((t, comissao_linha(bruto, referencia) - valor))
        if cond:
            try:
                dispensada = comissao_linha(bruto, taxa_planilha(t["cnpj"], t["faixa"], dia, entrada.contratos)) - valor
            except SemTaxa:
                dispensada = ZERO
            por_condicao[(cond["cnpj"], cond["faixa"])].append((t, dispensada))

    comissoes = [{"id_saida": id_comissao(comp, cnpj), "cnpj": cnpj, "lojista": nomes[cnpj],
                  "linha_negocio": LINHA_NEGOCIO, "comissao_brl": valor} for cnpj, valor in sorted(total.items())]

    for codigo, linhas in sorted(fora.items()):
        status = linhas[0]["status_ec"]
        pendencia(f"EC_{status}", codigo, sum((Decimal(t["valor_bruto"]) for t in linhas), ZERO),
                  f"EC {codigo} ({linhas[0]['nome_estabelecimento']}) com status {status}: {len(linhas)} transações "
                  f"fora da comissão; valor = soma do bruto. {ecs.get(codigo, {}).get('observacao', '')}".strip(),
                  QUEM_DECIDE_EC.get(status, "Financeiro"), [(t, Decimal(t["valor_bruto"])) for t in linhas])

    # Nota: zero ou negativo não emite, e o negativo não passa para o mês seguinte sozinho (Helena)
    for c in comissoes:
        if c["comissao_brl"] > 0:
            continue
        linhas = [(t, v) for linhas_ec in por_ec.values() for t, v in linhas_ec if t["cnpj"] == c["cnpj"]]
        pendencia("COMISSAO_NAO_POSITIVA", c["cnpj"], c["comissao_brl"],
                  f"Comissão de checkout de {c['lojista']} no mês é {c['comissao_brl']}: não emite nota, "
                  "e o saldo não é levado para o mês seguinte automaticamente.", "Financeiro", linhas)

    # R29: o contrato decide. A Orbe cobrou diferente do contrato: contestar a Orbe e ressarcir o lojista
    for cnpj, linhas in sorted(cobrado_a_mais.items()):
        valor = sum((v for _, v in linhas), ZERO)
        if valor:
            pendencia("CONTESTACAO_ORBE", cnpj, valor,
                      f"A Orbe cobrou de {nomes.get(cnpj, cnpj)} {valor} acima do contrato em {len(linhas)} transações "
                      "(ver divergencias_taxa): contestar a Orbe, ressarcir o lojista e corrigir a taxa cadastrada "
                      "na Orbe (R5, R29).", "Financeiro", linhas)

    for (cnpj, faixa), linhas in sorted(cobrado_na_concessao.items()):
        valor = sum((v for _, v in linhas), ZERO)
        pendencia("DEVOLUCAO_CONDICAO", f"{cnpj}/{faixa}", valor,
                  f"{nomes.get(cnpj, cnpj)} tem condição comercial fora do contrato (config/condicoes_especiais.csv), "
                  f"mas a Orbe cobrou {valor} em {len(linhas)} transações. A devolução é da Tarvo (R28, R29); "
                  "valor = o que a Orbe cobrou (valor_taxa).", "Financeiro", linhas)

    # Taxa da planilha sob suspeita (config/taxas_a_confirmar.csv): a comissão segue a planilha; a pendência mostra
    # quanto ela mudaria se a taxa de referência for a certa (P15, Fluente)
    for x in entrada.taxas_a_confirmar:
        linhas = a_confirmar.get((x["cnpj"], x["faixa"]), [])
        pendencia("TAXA_A_CONFIRMAR", f"{x['cnpj']}/{x['faixa']}", sum((v for _, v in linhas), ZERO),
                  f"{nomes.get(x['cnpj'], x['cnpj'])}: {x['motivo']}. Confirmar a taxa de {x['faixa']}; a comissão foi "
                  f"calculada pela planilha, e o valor é quanto ela mudaria a {x['taxa_referencia_pct']}% "
                  f"({x['fonte']}).", x["quem_decide"], linhas)

    # Decisões do financeiro que só existem em config/ porque faltam na planilha de taxas (seção 3.1 do HIPOTESES)
    for m in entrada.mapeamento:
        if m.get("pendencia_financeiro") and m["status"] == "CONFIRMADO":
            linhas = por_ec.get(m["ec"], [])
            pendencia("CADASTRO_EC", m["ec"], sum((v for _, v in linhas), ZERO),
                      f"{m['pendencia_financeiro']} Hoje o EC é ligado ao CNPJ {m['cnpj']} só por config/mapeamento_ec.csv "
                      f"({m['fonte']}); valor = comissão que depende desse mapeamento.", "Financeiro", linhas)
    for cond in entrada.condicoes:
        if cond.get("pendencia_financeiro"):
            linhas = por_condicao.get((cond["cnpj"], cond["faixa"]), [])
            pendencia("CADASTRO_CONDICAO", f"{cond['cnpj']}/{cond['faixa']}", sum((v for _, v in linhas), ZERO),
                      f"{cond['pendencia_financeiro']} Hoje a taxa de {cond['taxa_pct']}% vem só de "
                      f"config/condicoes_especiais.csv ({cond['fonte']}); valor = comissão que a planilha cobraria.",
                      "Financeiro", linhas)
    # Ordem estável: a mesma entrada gera sempre os mesmos arquivos (R12)
    return Resultado(comissoes=comissoes,
                     rastro=sorted(rastro, key=lambda x: (x["id_saida"], x["ref_origem"])),
                     pendencias=sorted(pendencias, key=lambda x: x["id_saida"]),
                     divergencias=sorted(divergencias, key=lambda x: x["id_saida"]))


def _rastro(id_saida: str, t: dict, valor: Decimal) -> dict:
    return {"id_saida": id_saida, "arquivo_origem": t["arquivo_origem"], "ref_origem": t["id_transacao"], "valor": valor}
