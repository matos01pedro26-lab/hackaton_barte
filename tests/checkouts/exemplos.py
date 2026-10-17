"""Linhas mínimas no formato das tabelas de data/ e config/, para montar cenários nos testes."""
from src.checkouts.comissao import Entrada

CNPJ_A = "11111111000111"
CNPJ_B = "22222222000122"


def transacao(id_transacao, cnpj=CNPJ_A, faixa="credito_a_vista", bruto="100.00", data="2026-09-10",
              tipo="VENDA", ec="1000000001", status_ec="CONFIRMADO", data_venda_original=""):
    return {
        "arquivo_origem": "01_orbe_relatorio_comissoes_set2026.csv", "id_transacao": id_transacao,
        "data_movimento": data, "ec": ec, "status_ec": status_ec, "cnpj": cnpj if status_ec == "CONFIRMADO" else "",
        "nome_estabelecimento": "LOJA", "tipo_lancamento": tipo, "faixa": faixa, "valor_bruto": bruto,
        "data_venda_original": data_venda_original,
    }


def contrato(cnpj=CNPJ_A, ini="2026-01-01", fim="", linha="10", **taxas):
    base = {"taxa_debito_pct": "1.49", "taxa_credito_vista_pct": "2.69", "taxa_credito_2_6x_pct": "3.19",
            "taxa_credito_7_12x_pct": "3.79", "taxa_pix_pct": "0.89", "taxa_antecipacao_pct": "2.1"}
    base.update(taxas)
    return {"cnpj": cnpj, "vigencia_ini": ini, "vigencia_fim": fim, "linha_planilha": linha, **base}


def condicao(cnpj=CNPJ_A, faixa="TODAS", taxa="0", ini="2026-09-01", fim="2026-12-31",
             pendencia="Registrar a condição na planilha"):
    return {"cnpj": cnpj, "faixa": faixa, "taxa_pct": taxa, "vigencia_ini": ini, "vigencia_fim": fim,
            "fonte": "Helena (financeiro)", "pendencia_financeiro": pendencia}


def mapeamento(codigo, cnpj, status="CONFIRMADO", pendencia="Preencher o EC na planilha"):
    return {"ec": codigo, "cnpj": cnpj, "status": status, "fonte": "Helena (financeiro)",
            "pendencia_financeiro": pendencia}


def lojista(cnpj=CNPJ_A, nome="Loja A Ltda"):
    return {"cnpj": cnpj, "nome_canonico": nome}


def ec(codigo="1000000001", cnpj=CNPJ_A, status="CONFIRMADO", fonte="tabela_taxas", observacao=""):
    return {"ec": codigo, "status": status, "cnpj": cnpj, "fonte_mapeamento": fonte, "observacao": observacao}


def entrada(transacoes, contratos=None, lojistas=None, ecs=None, mapeamento=None, condicoes=None):
    return Entrada(
        competencia="2026-09",
        transacoes=transacoes,
        contratos=contratos if contratos is not None else [contrato()],
        lojistas=lojistas if lojistas is not None else [lojista(), lojista(CNPJ_B, "Loja B Ltda")],
        ecs=ecs if ecs is not None else [ec()],
        mapeamento=mapeamento or [],
        condicoes=condicoes or [],
    )
