"""Orquestra a remessa: lê data/, classifica, calcula e grava os parciais. Nenhum cálculo fora dos módulos de regra."""
from __future__ import annotations

from collections import Counter
from decimal import Decimal
from pathlib import Path

from .comissao import calcular_comissoes
from .config import carregar_config
from .divergencia import acima_da_tolerancia, calcular_diferencas, divergencias
from .leitura import ler_contratos, ler_nomes_lojistas, ler_operacoes
from .pendencias import montar_pendencias
from .regras import Classe, classificar, indexar_contratos
from .saida import gravar, validar_rastro


def executar(mes: str, dados: Path, saida: Path, config: Path) -> dict[str, int]:
    cfg = carregar_config(config)
    ops = ler_operacoes(Path(dados) / "fato_ponte.csv")
    contratos = indexar_contratos(ler_contratos(Path(dados) / "dim_contrato_taxa.csv"))
    nomes = ler_nomes_lojistas(Path(dados) / "dim_lojista.csv")

    classificadas = [classificar(op, mes, cfg) for op in ops]
    comissoes, rastro_com, comissao_por_op = calcular_comissoes(classificadas, nomes, cfg)
    total = sum((l["comissao_brl"] for l in comissoes), Decimal("0.00"))

    diferencas, sem_contrato = calcular_diferencas(classificadas, contratos, cfg)
    linhas_div, rastro_div = divergencias(diferencas, cfg)
    divergentes = [d for d in diferencas if acima_da_tolerancia(d, cfg)]

    pendencias, rastro_pend = montar_pendencias(classificadas, diferencas, divergentes, sem_contrato,
                                                comissao_por_op, total, mes, cfg)
    rastro = rastro_com + rastro_div + rastro_pend
    validar_rastro({"comissoes": (comissoes, "comissao_brl"), "divergencias": (linhas_div, "diferenca_brl"),
                    "pendencias": (pendencias, "valor_brl")}, rastro)

    por_classe = Counter(c.classe for c in classificadas)
    resumo = [{"item": "mes", "valor": mes}, {"item": "operacoes_lidas", "valor": len(ops)},
              *({"item": f"operacoes_{k.value.lower()}", "valor": por_classe.get(k, 0)} for k in Classe),
              {"item": "total_participacao_brl", "valor": total},
              {"item": "tolerancia_brl", "valor": cfg.tolerancia_brl},
              {"item": "tolerancia_pp", "valor": cfg.tolerancia_pp},
              {"item": "divergencias_reportadas", "valor": len(linhas_div)},
              {"item": "pendencias", "valor": len(pendencias)}]
    return gravar(saida, comissoes, linhas_div, pendencias, rastro, resumo)
