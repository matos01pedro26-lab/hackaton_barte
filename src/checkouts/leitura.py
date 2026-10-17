"""Leitura das tabelas padronizadas (data/, geradas por src.ingestao) e das decisões humanas (config/)."""
from __future__ import annotations

import csv
import io
from pathlib import Path

from src.utils import ler_texto

from .comissao import Entrada


def ler_tabela(caminho: Path, obrigatorio: bool = True) -> list[dict]:
    caminho = Path(caminho)
    if not caminho.exists():
        if obrigatorio:
            raise FileNotFoundError(f"Tabela não encontrada: {caminho.resolve()} (rode antes: python -m src.ingestao)")
        return []
    texto, _ = ler_texto(caminho)
    return [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(io.StringIO(texto), delimiter=";")]


def ler_entrada(mes: str, dados: Path, config: Path) -> Entrada:
    dados, config = Path(dados), Path(config)
    return Entrada(
        competencia=mes,
        transacoes=[t for t in ler_tabela(dados / "fato_orbe.csv") if t["competencia"] == mes],
        contratos=ler_tabela(dados / "dim_contrato_taxa.csv"),
        lojistas=ler_tabela(dados / "dim_lojista.csv"),
        ecs=ler_tabela(dados / "dim_ec.csv"),
        mapeamento=ler_tabela(config / "mapeamento_ec.csv", obrigatorio=False),
        condicoes=ler_tabela(config / "condicoes_especiais.csv", obrigatorio=False),
        taxas_a_confirmar=ler_tabela(config / "taxas_a_confirmar.csv", obrigatorio=False),
    )
