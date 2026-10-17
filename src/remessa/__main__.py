"""Uso (a partir da raiz do repositório):
    python -m src.remessa --mes 2026-09 --dados data --saida saida/parcial
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import executar


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m src.remessa", description="Fechamento da linha de remessa")
    p.add_argument("--mes", required=True, help="competência, AAAA-MM")
    p.add_argument("--dados", default="data", type=Path, help="pasta com as tabelas da ingestão")
    p.add_argument("--saida", default=Path("saida/parcial"), type=Path, help="pasta dos arquivos parciais")
    p.add_argument("--config", default=Path("config/remessa.json"), type=Path)
    args = p.parse_args(argv)
    for nome, n in executar(args.mes, args.dados, args.saida, args.config).items():
        print(f"  {nome:22} {n:4} linhas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
