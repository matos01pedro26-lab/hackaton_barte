"""Leitura das tabelas prontas de data/. Dinheiro e taxas viram Decimal a partir do texto, nunca de float."""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..utils import ler_texto


def _dec(valor: str) -> Decimal | None:
    t = (valor or "").strip()
    if t == "":
        return None
    try:
        return Decimal(t)
    except InvalidOperation:
        raise ValueError(f"Valor numérico inválido na tabela de dados: {valor!r}") from None


def ler_tabela(caminho: Path) -> list[dict]:
    texto, _ = ler_texto(caminho)
    return [{k: (v or "").strip() for k, v in linha.items()}
            for linha in csv.DictReader(io.StringIO(texto), delimiter=";")]


@dataclass(frozen=True)
class Operacao:
    num_op: str
    arquivo_origem: str
    linha_origem: str
    data_contratacao: str
    cnpj: str
    cliente_nome: str
    valor_me: Decimal
    ptax: Decimal
    spread_brl: Decimal
    spread_pct: Decimal | None
    status_compliance: str
    observacao: str
    flag_duplicata: bool


@dataclass(frozen=True)
class Contrato:
    cnpj: str
    nome_tabela: str
    vigencia_ini: str
    vigencia_fim: str
    spread_remessa_pct: Decimal | None
    spread_remessa_regra: str


def ler_operacoes(caminho: Path) -> list[Operacao]:
    return [Operacao(
        num_op=r["num_op"], arquivo_origem=r["arquivo_origem"], linha_origem=r["linha_origem"],
        data_contratacao=r["data_contratacao"], cnpj=r["cnpj"], cliente_nome=r["cliente_nome"],
        valor_me=_dec(r["valor_me"]), ptax=_dec(r["ptax"]), spread_brl=_dec(r["spread_brl"]),
        spread_pct=_dec(r["spread_pct"]), status_compliance=r["status_compliance"],
        observacao=r["observacao"], flag_duplicata=r["flag_duplicata"] == "S",
    ) for r in ler_tabela(caminho)]


def ler_contratos(caminho: Path) -> list[Contrato]:
    return [Contrato(
        cnpj=r["cnpj"], nome_tabela=r["nome_tabela"], vigencia_ini=r["vigencia_ini"], vigencia_fim=r["vigencia_fim"],
        spread_remessa_pct=_dec(r["spread_remessa_pct"]), spread_remessa_regra=r["spread_remessa_regra"],
    ) for r in ler_tabela(caminho)]


def ler_nomes_lojistas(caminho: Path) -> dict[str, str]:
    """CNPJ -> nome canônico. Só lojistas com CNPJ (os ECs sem cadastro, como a Atlas, não entram)."""
    return {r["cnpj"]: r["nome_canonico"] for r in ler_tabela(caminho) if r["cnpj"]}
