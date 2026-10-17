"""Comissão da Tarvo na remessa: 50% do Spread R$ realizado, por operação, arredondado por operação e somado por lojista."""
from __future__ import annotations

from decimal import Decimal

from .config import Config
from .ids import id_comissao
from .regras import Classe, OpClassificada, arredondar

ELEGIVEIS = (Classe.NORMAL, Classe.AJUSTE)


def comissao_operacao(spread_brl: Decimal, cfg: Config) -> Decimal:
    return arredondar(spread_brl * cfg.participacao_tarvo)


def calcular_comissoes(classificadas: list[OpClassificada], nomes: dict[str, str], cfg: Config,
                       mes: str) -> tuple[list[dict], list[dict], dict[str, Decimal]]:
    """Devolve (linhas por lojista, linhas de rastro, comissão por operação). Uma linha por lojista, id_saida = REM-AAAA-MM-<cnpj>."""
    por_lojista: dict[str, dict] = {}
    rastro: list[dict] = []
    por_op: dict[str, Decimal] = {}
    for c in classificadas:
        if c.classe not in ELEGIVEIS:
            continue
        op = c.op
        valor = comissao_operacao(op.spread_brl, cfg)
        por_op[op.num_op] = valor
        id_saida = id_comissao(mes, op.cnpj)
        linha = por_lojista.setdefault(id_saida, {
            "id_saida": id_saida, "cnpj": op.cnpj, "lojista": nomes.get(op.cnpj, op.cliente_nome),
            "linha_negocio": "REMESSA", "comissao_brl": Decimal("0.00"), "n_operacoes": 0, "n_ajustes": 0,
        })
        linha["comissao_brl"] += valor
        linha["n_operacoes"] += 1
        linha["n_ajustes"] += 1 if c.classe is Classe.AJUSTE else 0
        rastro.append({"id_saida": id_saida, "arquivo_origem": op.arquivo_origem, "ref_origem": op.num_op,
                       "valor": valor, "ref_original": c.op_original})
    linhas = sorted(por_lojista.values(), key=lambda l: l["cnpj"])
    return linhas, rastro, por_op
