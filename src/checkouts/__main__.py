"""Comissão de checkout do mês.

Uso (a partir da raiz do repositório, depois de python -m src.ingestao):
    python -m src.checkouts --mes 2026-09 --entrada data --config config --saida saida/checkouts

Grava comissoes_por_lojista.csv, rastro.csv e pendencias.csv (só a parte do checkout; a consolidação com
remessa e bancos é feita na integração).
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .comissao import Resultado, calcular
from .leitura import ler_entrada
from .saida import gravar


def executar(mes: str, entrada: Path, config: Path, saida: Path) -> Resultado:
    resultado = calcular(ler_entrada(mes, entrada, config))
    gravar(resultado, saida)
    return resultado


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Comissão de checkout por lojista, com rastro e pendências.")
    ap.add_argument("--mes", default="2026-09", help="competência AAAA-MM")
    ap.add_argument("--entrada", default="data", help="pasta com as tabelas geradas por src.ingestao")
    ap.add_argument("--config", default="config", help="pasta com mapeamento_ec.csv e condicoes_especiais.csv")
    ap.add_argument("--saida", default="saida/checkouts", help="pasta onde os CSVs serão gravados")
    a = ap.parse_args(argv)
    r = executar(a.mes, Path(a.entrada), Path(a.config), Path(a.saida))
    total = sum(c["comissao_brl"] for c in r.comissoes)
    print(f"Checkout {a.mes}: {len(r.comissoes)} lojistas, comissão total R$ {total}, "
          f"{len(r.pendencias)} pendências. Arquivos em {Path(a.saida).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
