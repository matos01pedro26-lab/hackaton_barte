"""Parâmetros do módulo de remessa. Nada de regra solta no código: o que pode mudar de um mês para o outro vive em config/remessa.json."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class Config:
    participacao_tarvo: Decimal
    spread_padrao_pct: Decimal
    tolerancia_brl: Decimal
    tolerancia_pp: Decimal
    padrao_ajuste: re.Pattern
    quem_decide: dict[str, str]


def carregar_config(caminho: Path) -> Config:
    bruto = json.loads(Path(caminho).read_text(encoding="utf-8"))
    return Config(
        participacao_tarvo=Decimal(bruto["participacao_tarvo"]),
        spread_padrao_pct=Decimal(bruto["spread_padrao_pct"]),
        tolerancia_brl=Decimal(bruto["tolerancia_brl"]),
        tolerancia_pp=Decimal(bruto.get("tolerancia_pp", "0")),
        padrao_ajuste=re.compile(bruto["padrao_ajuste"], re.IGNORECASE),
        quem_decide=dict(bruto["quem_decide"]),
    )
