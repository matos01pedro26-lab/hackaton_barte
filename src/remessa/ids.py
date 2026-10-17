"""Formato dos id_saida da remessa, no mesmo padrão do checkout (CHK-AAAA-MM-<cnpj>, PEN-CHK-AAAA-MM-<tipo>-<ref>).

Os ids são chaves naturais: CNPJ do lojista ou Nº da operação da Ponte, nunca UUID. Estáveis de um mês para o outro.
"""
from __future__ import annotations


def id_comissao(mes: str, cnpj: str) -> str:
    return f"REM-{mes}-{cnpj}"


def id_divergencia(mes: str, num_op: str) -> str:
    return f"DIV-REM-{mes}-{num_op}"


def id_pendencia(mes: str, tipo: str, ref: str) -> str:
    return f"PEN-REM-{mes}-{tipo}-{ref}"


def id_nota(mes: str, cnpj_tomador: str) -> str:
    return f"NF-REM-{mes}-{cnpj_tomador}"
