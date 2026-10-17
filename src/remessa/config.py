"""Parâmetros do módulo de remessa. Nada de regra solta no código.

Duas fontes, cada valor em um lugar só:
  * config/parametros.csv: parâmetros compartilhados com a ingestão (spread padrão e tolerância do spread, com fonte e quem aprovou);
  * config/remessa.json: o que é só da remessa (participação da Tarvo, tolerância em reais, padrão do ajuste, quem decide).
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from ..utils import ler_texto


@dataclass(frozen=True)
class Config:
    participacao_tarvo: Decimal
    spread_padrao_pct: Decimal
    tolerancia_brl: Decimal
    tolerancia_pp: Decimal
    padrao_ajuste: re.Pattern
    tomador_cnpj: str
    tomador_nome: str
    quem_decide: dict[str, str]


def ler_parametros(caminho: Path) -> dict[str, str]:
    texto, _ = ler_texto(caminho)
    return {l["chave"].strip(): l["valor"].strip() for l in csv.DictReader(texto.splitlines(), delimiter=";") if l.get("chave")}


def carregar_config(caminho: Path, parametros: Path | None = None) -> Config:
    caminho = Path(caminho)
    bruto = json.loads(caminho.read_text(encoding="utf-8"))
    comuns = ler_parametros(Path(parametros) if parametros else caminho.parent / "parametros.csv")
    return Config(
        participacao_tarvo=Decimal(bruto["participacao_tarvo"]),
        spread_padrao_pct=Decimal(comuns["spread_padrao_pct"]),
        tolerancia_brl=Decimal(bruto["tolerancia_brl"]),
        tolerancia_pp=Decimal(comuns["tolerancia_spread_pp"]),
        padrao_ajuste=re.compile(bruto["padrao_ajuste"], re.IGNORECASE),
        tomador_cnpj=bruto["tomador"]["cnpj"],
        tomador_nome=bruto["tomador"]["nome"],
        quem_decide=dict(bruto["quem_decide"]),
    )
