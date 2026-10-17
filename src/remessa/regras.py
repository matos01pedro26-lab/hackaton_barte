"""Regras de elegibilidade das operações da Ponte e escolha do spread contratado.

Regras vindas do financeiro (canal #tarvo-financeiro):
  * vale a data de contratação;
  * operação repetida conta uma vez (o Nº de operação é único);
  * spread negativo não é aceito: fica fora da comissão e da nota;
  * linha "AJUSTE REF PC-..." entra no mês em que aparece e abate a participação;
  * status de compliance ("APROVADO C/ RESSALVA") não muda nada;
  * spread em branco ou "padrão" vale o spread padrão da configuração.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from .config import Config
from .leitura import Contrato, Operacao

CENTAVO = Decimal("0.01")


class Classe(str, Enum):
    NORMAL = "NORMAL"
    AJUSTE = "AJUSTE"
    SPREAD_NEGATIVO = "SPREAD_NEGATIVO"
    DUPLICATA = "DUPLICATA"
    FORA_COMPETENCIA = "FORA_COMPETENCIA"


@dataclass(frozen=True)
class OpClassificada:
    op: Operacao
    classe: Classe
    op_original: str = ""


def arredondar(valor: Decimal) -> Decimal:
    """Arredondamento comum para o centavo: meio centavo vai para longe do zero (-0,005 vira -0,01)."""
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def classificar(op: Operacao, mes: str, cfg: Config) -> OpClassificada:
    if op.flag_duplicata:
        return OpClassificada(op, Classe.DUPLICATA)
    if not op.data_contratacao.startswith(mes):
        return OpClassificada(op, Classe.FORA_COMPETENCIA)
    ajuste = cfg.padrao_ajuste.search(op.observacao)
    if ajuste:
        return OpClassificada(op, Classe.AJUSTE, op_original=ajuste.group(1))
    if op.spread_brl < 0:
        return OpClassificada(op, Classe.SPREAD_NEGATIVO)
    return OpClassificada(op, Classe.NORMAL)


def indexar_contratos(contratos: list[Contrato]) -> dict[str, list[Contrato]]:
    por_cnpj: dict[str, list[Contrato]] = {}
    for c in contratos:
        por_cnpj.setdefault(c.cnpj, []).append(c)
    return por_cnpj


def contrato_vigente(op: Operacao, por_cnpj: dict[str, list[Contrato]]) -> Contrato | None:
    """Linha da tabela de taxas vigente na data de contratação. Vigência em branco é aberta; os limites são inclusivos."""
    for c in por_cnpj.get(op.cnpj, []):
        if (c.vigencia_ini == "" or c.vigencia_ini <= op.data_contratacao) and \
           (c.vigencia_fim == "" or op.data_contratacao <= c.vigencia_fim):
            return c
    return None


def spread_contratado(contrato: Contrato, cfg: Config) -> tuple[Decimal, str]:
    """(spread em %, regra). Explícito vem da tabela; em branco ou "padrão" usa o padrão da configuração."""
    if contrato.spread_remessa_pct is not None:
        return contrato.spread_remessa_pct, "EXPLICITO"
    return cfg.spread_padrao_pct, "PADRAO"
