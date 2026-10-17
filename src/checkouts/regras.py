"""Regras de negócio do checkout confirmadas pelo financeiro (ver HIPOTESES.md). Funções puras, sem I/O."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

CENTAVO = Decimal("0.01")

FAIXA_COLUNA = {
    "debito": "taxa_debito_pct", "credito_a_vista": "taxa_credito_vista_pct",
    "credito_2_6x": "taxa_credito_2_6x_pct", "credito_7_12x": "taxa_credito_7_12x_pct",
    "pix": "taxa_pix_pct", "antecipacao": "taxa_antecipacao_pct",
}


def arredondar(valor: Decimal) -> Decimal:
    """R8: arredondamento comum para o centavo, meio centavo para cima (e para baixo nos negativos)."""
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def comissao_linha(valor_bruto: Decimal, taxa_pct: Decimal) -> Decimal:
    """R1: valor bruto × taxa contratada, arredondado por linha. Estorno e reversão têm bruto negativo."""
    return arredondar(valor_bruto * taxa_pct / Decimal(100))


def data_da_taxa(transacao: dict) -> str:
    """Venda e antecipação: data do movimento (vigência da Bridge, Helena). Estorno e reversão: data da venda
    ou antecipação original (R2), que a Orbe informa em data_venda_original."""
    return transacao["data_venda_original"] or transacao["data_movimento"]


def vigente(inicio: str, fim: str, dia: str) -> bool:
    """Datas AAAA-MM-DD; início ou fim em branco = sem limite."""
    return (not inicio or inicio <= dia) and (not fim or dia <= fim)


class SemTaxa(Exception):
    """Não há uma única taxa contratada para a transação. Quem chama transforma em pendência; nunca se chuta."""


def condicao_vigente(cnpj: str, faixa: str, dia: str, condicoes: list[dict]) -> dict | None:
    """Condição especial de config/condicoes_especiais.csv (R24) que vale para a transação, se houver."""
    especiais = [c for c in condicoes if c["cnpj"] == cnpj and c["faixa"] in ("TODAS", faixa)
                 and vigente(c["vigencia_ini"], c["vigencia_fim"], dia)]
    if len(especiais) > 1:
        raise SemTaxa(f"{len(especiais)} condições especiais vigentes em {dia} para o CNPJ {cnpj}, faixa {faixa}")
    return especiais[0] if especiais else None


def taxa_contratada(cnpj: str, faixa: str, dia: str, contratos: list[dict], condicoes: list[dict]) -> Decimal:
    """A condição especial vale antes da planilha, dentro da vigência dela."""
    especial = condicao_vigente(cnpj, faixa, dia, condicoes)
    if especial:
        return Decimal(especial["taxa_pct"])
    return taxa_planilha(cnpj, faixa, dia, contratos)


def taxa_planilha(cnpj: str, faixa: str, dia: str, contratos: list[dict]) -> Decimal:
    vigentes = [c for c in contratos if c["cnpj"] == cnpj and vigente(c["vigencia_ini"], c["vigencia_fim"], dia)]
    if len(vigentes) != 1:
        raise SemTaxa(f"{len(vigentes)} contratos vigentes em {dia} para o CNPJ {cnpj} na planilha de taxas")
    taxa = vigentes[0][FAIXA_COLUNA[faixa]]
    if not taxa:
        raise SemTaxa(f"taxa de {faixa} em branco na planilha (linha {vigentes[0]['linha_planilha']}) "
                      f"para o CNPJ {cnpj}")
    return Decimal(taxa)
