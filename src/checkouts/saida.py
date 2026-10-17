"""Gravação dos CSVs do checkout no formato do edital: ';', ponto decimal, valores com 2 casas."""
from __future__ import annotations

from pathlib import Path

from src.utils import escrever_csv

from .comissao import Resultado
from .regras import CENTAVO

COL_COMISSOES = ["id_saida", "cnpj", "lojista", "linha_negocio", "comissao_brl"]
COL_RASTRO = ["id_saida", "arquivo_origem", "ref_origem", "valor"]
COL_PENDENCIAS = ["id_saida", "tipo", "ref_origem", "valor_brl", "motivo", "quem_decide"]


def _centavos(linhas: list[dict], campo: str) -> list[dict]:
    return [{**l, campo: l[campo].quantize(CENTAVO)} for l in linhas]


def gravar(resultado: Resultado, saida: Path) -> dict[str, int]:
    saida = Path(saida)
    return {
        "comissoes_por_lojista": escrever_csv(saida / "comissoes_por_lojista.csv",
                                              _centavos(resultado.comissoes, "comissao_brl"), COL_COMISSOES),
        "rastro": escrever_csv(saida / "rastro.csv", _centavos(resultado.rastro, "valor"), COL_RASTRO),
        "pendencias": escrever_csv(saida / "pendencias.csv", _centavos(resultado.pendencias, "valor_brl"),
                                   COL_PENDENCIAS),
    }
