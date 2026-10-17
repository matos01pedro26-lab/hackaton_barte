"""Divergência de spread: o spread que a Ponte aplicou contra o spread contratado.

diferenca = Spread R$ da Ponte - (spread contratado % x Valor ME x PTAX), valor cheio (quem pagou a mais foi o lojista).
Só reporta quando |diferenca| passa da tolerância da configuração (começa em zero; o estudo exploratório decide o valor).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .config import Config
from .leitura import Contrato
from .regras import Classe, OpClassificada, arredondar, contrato_vigente, spread_contratado

COMPARAVEIS = (Classe.NORMAL, Classe.SPREAD_NEGATIVO)


@dataclass(frozen=True)
class Diferenca:
    classificada: OpClassificada
    contratado_pct: Decimal
    regra: str
    base_brl: Decimal
    diferenca_brl: Decimal


def calcular_diferencas(classificadas: list[OpClassificada], por_cnpj: dict[str, list[Contrato]],
                        cfg: Config) -> tuple[list[Diferenca], list[OpClassificada]]:
    """Diferença de todas as operações comparáveis (sem filtrar por tolerância) e as que não têm contrato vigente."""
    diferencas: list[Diferenca] = []
    sem_contrato: list[OpClassificada] = []
    for c in classificadas:
        if c.classe not in COMPARAVEIS:
            continue
        contrato = contrato_vigente(c.op, por_cnpj)
        if contrato is None:
            sem_contrato.append(c)
            continue
        pct, regra = spread_contratado(contrato, cfg)
        base = c.op.valor_me * c.op.ptax
        diferencas.append(Diferenca(c, pct, regra, base, arredondar(c.op.spread_brl - pct / 100 * base)))
    return diferencas, sem_contrato


def divergencias(diferencas: list[Diferenca], cfg: Config) -> tuple[list[dict], list[dict]]:
    """Linhas de divergencias_taxa (parcial) e rastro. id_saida = Nº da operação."""
    linhas, rastro = [], []
    for d in diferencas:
        if abs(d.diferenca_brl) <= cfg.tolerancia_brl:
            continue
        op = d.classificada.op
        aplicada = op.spread_pct if op.spread_pct is not None else op.spread_brl / d.base_brl * 100
        linhas.append({
            "id_saida": op.num_op, "cnpj": op.cnpj, "linha_negocio": "REMESSA", "ref_origem": op.num_op,
            "taxa_contratada_pct": d.contratado_pct, "taxa_aplicada_pct": aplicada, "diferenca_brl": d.diferenca_brl,
            "classe": d.classificada.classe.value, "regra_spread": d.regra,
            "spread_brl": op.spread_brl, "base_brl": arredondar(d.base_brl),
        })
        rastro.append({"id_saida": op.num_op, "arquivo_origem": op.arquivo_origem, "ref_origem": op.num_op,
                       "valor": d.diferenca_brl, "ref_original": ""})
    return linhas, rastro
