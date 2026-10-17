"""Gravação dos arquivos parciais de remessa e validação do rastro."""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from ..utils import escrever_csv

COL_COMISSOES = ["id_saida", "cnpj", "lojista", "linha_negocio", "comissao_brl", "n_operacoes", "n_ajustes"]
COL_DIVERGENCIAS = ["id_saida", "cnpj", "linha_negocio", "ref_origem", "taxa_contratada_pct", "taxa_aplicada_pct",
                    "diferenca_brl", "classe", "regra_spread", "spread_brl", "base_brl"]
COL_PENDENCIAS = ["id_saida", "tipo", "ref_origem", "valor_brl", "motivo", "quem_decide"]
COL_RASTRO = ["id_saida", "arquivo_origem", "ref_origem", "valor", "ref_original"]
COL_RESUMO = ["item", "valor"]


def validar_rastro(saidas: dict[str, tuple[list[dict], str]], rastro: list[dict]) -> None:
    """A soma do rastro de cada id_saida tem que bater com o número reportado, ao centavo.
    `saidas` mapeia nome -> (linhas, coluna do valor). Levanta ValueError listando o que não fecha."""
    soma: dict[str, Decimal] = {}
    for r in rastro:
        soma[r["id_saida"]] = soma.get(r["id_saida"], Decimal("0")) + r["valor"]
    erros = []
    reportados: set[str] = set()
    for nome, (linhas, coluna) in saidas.items():
        for l in linhas:
            reportados.add(l["id_saida"])
            esperado = l[coluna]
            achado = soma.get(l["id_saida"], Decimal("0"))
            if achado != esperado:
                erros.append(f"{nome} {l['id_saida']}: reportado={esperado} rastro={achado}")
    erros += [f"rastro sem número reportado: {i}" for i in sorted(set(soma) - reportados)]
    if erros:
        raise ValueError("Rastro não fecha com as saídas:\n  " + "\n  ".join(erros))


def gravar(pasta: Path, comissoes: list[dict], divergencias: list[dict], pendencias: list[dict],
           rastro: list[dict], resumo: list[dict]) -> dict[str, int]:
    pasta = Path(pasta)
    return {
        "remessa_comissoes": escrever_csv(pasta / "remessa_comissoes.csv", comissoes, COL_COMISSOES),
        "remessa_divergencias": escrever_csv(pasta / "remessa_divergencias.csv", divergencias, COL_DIVERGENCIAS),
        "remessa_pendencias": escrever_csv(pasta / "remessa_pendencias.csv", pendencias, COL_PENDENCIAS),
        "remessa_rastro": escrever_csv(pasta / "remessa_rastro.csv", rastro, COL_RASTRO),
        "remessa_resumo": escrever_csv(pasta / "remessa_resumo.csv", resumo, COL_RESUMO),
    }
