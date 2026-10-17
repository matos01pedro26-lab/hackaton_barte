"""Nota de remessa: uma só por mês, tomadora a Ponte Câmbio, pelo total da participação da Tarvo (regra da Helena).

Zero ou negativo não emite nota (o saldo vira pendência para a Helena e não passa para o mês seguinte).
O rastro da nota é o mesmo da comissão: uma linha por operação (inclusive os ajustes, que abatem o total).
"""
from __future__ import annotations

from decimal import Decimal

from .config import Config
from .ids import id_nota


def montar_nota(total: Decimal, rastro_comissoes: list[dict], mes: str, cfg: Config) -> tuple[list[dict], list[dict]]:
    if total <= 0:
        return [], []
    id_saida = id_nota(mes, cfg.tomador_cnpj)
    ano, mm = mes.split("-")
    linha = {
        "id_saida": id_saida, "tomador_cnpj": cfg.tomador_cnpj, "tomador": cfg.tomador_nome, "linha_negocio": "REMESSA",
        "valor_brl": total,
        "discriminacao": f"Intermediação de operações de câmbio: participação da Tarvo no spread, competência {mm}/{ano}",
    }
    rastro = [{**r, "id_saida": id_saida} for r in rastro_comissoes]
    return [linha], rastro
