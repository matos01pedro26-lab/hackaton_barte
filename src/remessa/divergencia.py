"""Divergência de spread: o spread que a Ponte aplicou contra o spread contratado.

diferenca = Spread R$ da Ponte - (spread contratado % x Valor ME x PTAX), valor cheio (quem pagou a mais foi o lojista).
Só reporta quando a diferença passa das DUAS tolerâncias da configuração: em reais (tolerancia_brl) e em pontos
percentuais de spread (tolerancia_pp). Dentro de qualquer uma delas é ruído de arredondamento da Ponte.
Ambas começam em zero; o estudo exploratório (notebooks/remessa_tolerancia.ipynb) decide o valor.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .config import Config
from .ids import id_divergencia
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

    @property
    def desvio_pp(self) -> Decimal:
        """Spread aplicado menos contratado, em pontos percentuais, sobre a base Valor ME x PTAX."""
        return self.classificada.op.spread_brl / self.base_brl * 100 - self.contratado_pct


def acima_da_tolerancia(d: Diferenca, cfg: Config) -> bool:
    return abs(d.diferenca_brl) > cfg.tolerancia_brl and abs(d.desvio_pp) > cfg.tolerancia_pp


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


def divergencias(diferencas: list[Diferenca], cfg: Config, mes: str) -> tuple[list[dict], list[dict]]:
    """Linhas de divergencias_taxa (parcial) e rastro. id_saida = DIV-REM-AAAA-MM-<Nº da operação>."""
    linhas, rastro = [], []
    for d in diferencas:
        if not acima_da_tolerancia(d, cfg):
            continue
        op = d.classificada.op
        aplicada = op.spread_pct if op.spread_pct is not None else op.spread_brl / d.base_brl * 100
        id_saida = id_divergencia(mes, op.num_op)
        linhas.append({
            "id_saida": id_saida, "cnpj": op.cnpj, "linha_negocio": "REMESSA", "ref_origem": op.num_op,
            "taxa_contratada_pct": d.contratado_pct, "taxa_aplicada_pct": aplicada, "diferenca_brl": d.diferenca_brl,
            "classe": d.classificada.classe.value, "regra_spread": d.regra,
            "spread_brl": op.spread_brl, "base_brl": arredondar(d.base_brl),
        })
        rastro.append({"id_saida": id_saida, "arquivo_origem": op.arquivo_origem, "ref_origem": op.num_op,
                       "valor": d.diferenca_brl, "ref_original": ""})
    return linhas, rastro
