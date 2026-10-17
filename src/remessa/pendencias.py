"""Pendências da remessa: tudo que exige uma pessoa. Cada uma tem motivo, valor e quem decide.

ref_origem pode listar várias origens separadas por '|' (o case aceita as duas formas); o rastro tem uma linha por origem.
"""
from __future__ import annotations

from decimal import Decimal

from .comissao import ELEGIVEIS
from .config import Config
from .divergencia import Diferenca
from .ids import id_nota, id_pendencia
from .regras import Classe, OpClassificada


def _pendencia(id_saida: str, tipo: str, refs: list[str], valor: Decimal, motivo: str, quem: str) -> dict:
    return {"id_saida": id_saida, "tipo": tipo, "ref_origem": "|".join(refs), "valor_brl": valor,
            "motivo": motivo, "quem_decide": quem}


def _rastro(id_saida: str, c: OpClassificada, valor: Decimal) -> dict:
    return {"id_saida": id_saida, "arquivo_origem": c.op.arquivo_origem, "ref_origem": c.op.num_op,
            "valor": valor, "ref_original": c.op_original}


def montar_pendencias(classificadas: list[OpClassificada], diferencas: list[Diferenca],
                      divergentes: list[Diferenca], sem_contrato: list[OpClassificada],
                      comissao_por_op: dict[str, Decimal], total_participacao: Decimal,
                      mes: str, cfg: Config) -> tuple[list[dict], list[dict]]:
    pend: list[dict] = []
    rastro: list[dict] = []
    ponte = cfg.quem_decide["contestacao_ponte"]

    for c in classificadas:
        op = c.op
        if c.classe is Classe.DUPLICATA:
            id_saida = id_pendencia(mes, "DUPLICATA", op.num_op)
            pend.append(_pendencia(id_saida, "DUPLICATA", [op.num_op], op.spread_brl,
                                   "Mesmo Nº de operação repetido no relatório da Ponte. Conta uma vez no fechamento; "
                                   "a repetida entra na lista para a Ponte corrigir o relatório.", ponte))
            rastro.append(_rastro(id_saida, c, op.spread_brl))
        elif c.classe is Classe.SPREAD_NEGATIVO:
            id_saida = id_pendencia(mes, "SPREAD_NEGATIVO", op.num_op)
            pend.append(_pendencia(id_saida, "SPREAD_NEGATIVO", [op.num_op], op.spread_brl,
                                   "Spread negativo no relatório (valor que aconteceu). Fora da comissão e da nota; "
                                   "a trava passou do prazo de 2 horas. Contestar com a Ponte.", ponte))
            rastro.append(_rastro(id_saida, c, op.spread_brl))
        elif c.classe is Classe.AJUSTE_NAO_RECONHECIDO:
            id_saida = id_pendencia(mes, "AJUSTE_NAO_RECONHECIDO", op.num_op)
            pend.append(_pendencia(id_saida, "AJUSTE_NAO_RECONHECIDO", [op.num_op], op.spread_brl,
                                   f"Observação \"{op.observacao}\" fala em ajuste, mas não segue o padrão "
                                   "\"AJUSTE REF PC-...\" e não diz qual operação ajusta (contratação "
                                   f"{op.data_contratacao}). Fora da comissão e da nota até a Helena decidir.", ponte))
            rastro.append(_rastro(id_saida, c, op.spread_brl))
        elif c.classe is Classe.FORA_COMPETENCIA:
            id_saida = id_pendencia(mes, "FORA_COMPETENCIA", op.num_op)
            pend.append(_pendencia(id_saida, "FORA_COMPETENCIA", [op.num_op], op.spread_brl,
                                   f"Data de contratação ({op.data_contratacao}) fora do mês {mes}. "
                                   "Não entra na comissão do mês.", ponte))
            rastro.append(_rastro(id_saida, c, op.spread_brl))

    for d in diferencas:
        if d.classificada.classe is Classe.SPREAD_NEGATIVO:
            op = d.classificada.op
            id_saida = id_pendencia(mes, "CONTESTACAO_ATE_CONTRATO", op.num_op)
            pend.append(_pendencia(id_saida, "CONTESTACAO_ATE_CONTRATO", [op.num_op], d.diferenca_brl,
                                   f"Diferença até o spread do contrato ({d.contratado_pct}% sobre a PTAX): "
                                   "o que se pede à Ponte, porque a trava deveria ter sido honrada.", ponte))
            rastro.append(_rastro(id_saida, d.classificada, d.diferenca_brl))

    por_lojista: dict[str, list[Diferenca]] = {}
    for d in divergentes:
        if d.classificada.classe is Classe.NORMAL:
            por_lojista.setdefault(d.classificada.op.cnpj, []).append(d)
    for cnpj, itens in sorted(por_lojista.items()):
        id_saida = id_pendencia(mes, "CONTESTACAO_PONTE", cnpj)
        total = sum((d.diferenca_brl for d in itens), Decimal("0.00"))
        pend.append(_pendencia(id_saida, "CONTESTACAO_PONTE", [d.classificada.op.num_op for d in itens], total,
                               "Spread aplicado pela Ponte diferente do contratado. Valor cheio pago a mais pelo "
                               "lojista; contestar com a Ponte e ressarcir o lojista.", ponte))
        rastro.extend(_rastro(id_saida, d.classificada, d.diferenca_brl) for d in itens)

    por_cnpj_sem: dict[str, list[OpClassificada]] = {}
    for c in sem_contrato:
        por_cnpj_sem.setdefault(c.op.cnpj, []).append(c)
    for cnpj, itens in sorted(por_cnpj_sem.items()):
        elegiveis = [c for c in itens if c.classe in ELEGIVEIS]
        if not elegiveis:
            continue
        id_saida = id_pendencia(mes, "CADASTRO_AUSENTE", cnpj)
        valor = sum((comissao_por_op[c.op.num_op] for c in elegiveis), Decimal("0.00"))
        pend.append(_pendencia(id_saida, "CADASTRO_AUSENTE", [c.op.num_op for c in elegiveis], valor,
                               "CNPJ com remessa na Ponte e sem linha vigente na tabela de taxas. A participação foi "
                               "calculada e entra na nota (a Ponte paga); falta o cadastro para comparar o spread.",
                               cfg.quem_decide["cadastro"]))
        rastro.extend(_rastro(id_saida, c, comissao_por_op[c.op.num_op]) for c in elegiveis)

    if total_participacao <= 0:
        id_saida = id_pendencia(mes, "NOTA_NAO_EMITIDA", cfg.tomador_cnpj)
        pend.append(_pendencia(id_saida, "NOTA_NAO_EMITIDA", [id_nota(mes, cfg.tomador_cnpj)], total_participacao,
                               "Participação do mês zerada ou negativa: não emite nota e o saldo não passa para o mês seguinte.",
                               cfg.quem_decide["nota"]))
        elegiveis = [c for c in classificadas if c.classe in ELEGIVEIS]
        if elegiveis:       # o saldo que não vira nota é a soma dessas operações (ajustes abatendo, por exemplo)
            rastro.extend(_rastro(id_saida, c, comissao_por_op[c.op.num_op]) for c in elegiveis)
        else:               # mês sem nenhuma operação elegível: uma linha explicando, para o rastro fechar em zero
            rastro.append({"id_saida": id_saida, "arquivo_origem": "(nenhuma operação elegível no mês)",
                           "ref_origem": id_nota(mes, cfg.tomador_cnpj), "valor": Decimal("0.00"), "ref_original": ""})
    return pend, rastro
