"""Classificação dos lançamentos dos extratos (Aurora e Meridiano) no plano de contas do ERP Fênix.

Uso (a partir da raiz, depois de python -m src.ingestao):
    python -m src.classificacao --mes 2026-09 --dados data --saida saida

Entrada:  data/fato_banco.csv e data/dim_plano_contas.csv (e data/controle_ingestao.csv só para conferir os saldos).
Saída:    lancamentos_classificados.csv, com as colunas do edital
          (id_saida; banco; ref_origem; data; descricao; valor; conta_codigo; metodo; confianca)
          e extras (conta_descricao, conta_banco, sentido, regra, premissa, observacao).

O que a conta_codigo representa (resposta do financeiro): a CONTRAPARTIDA do movimento no banco. Se o valor já estava
registrado (folha e tributos do mês anterior, comissão a receber da Ponte), o pagamento ou recebimento baixa a conta
onde estava e não vira receita ou despesa de novo. A outra perna é sempre a conta do banco (conta_banco).

Método:
  * REGRA  - a descrição do extrato casa com uma regra explícita da tabela REGRAS abaixo.
  * IA     - só se uma função sugestora for passada e a conta sugerida for analítica. Este repositório não chama nenhum
             modelo (não há chave), então hoje nenhum lançamento sai como IA.
  * HUMANO - nenhuma regra casou e não houve sugestão: conta_codigo fica vazio, confianca 0 e a linha vira pendência.

Só entram contas com ACEITA_LANCTO = S. Conta sintética nunca é gravada: a ingestão da regra e o resultado são
validados contra o plano e a execução para com erro se algo escapar.
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Callable

from .utils import escrever_csv, ler_texto

CENTAVO = Decimal("0.01")
BANCO_CONTA = {"AURORA": "1.1.01.001", "MERIDIANO": "1.1.01.002"}      # a outra perna do lançamento

COL_LANCAMENTOS = ["id_saida", "banco", "ref_origem", "data", "descricao", "valor", "conta_codigo", "metodo",
                   "confianca", "conta_descricao", "conta_banco", "sentido", "regra", "premissa", "observacao"]
COL_RASTRO = ["id_saida", "arquivo_origem", "ref_origem", "valor"]

PROVISAO = ("Já provisionado no fechamento do mês anterior (Helena, financeiro): o pagamento baixa a provisão e "
            "não vira despesa.")


@dataclass(frozen=True)
class Regra:
    id: str
    banco: str
    padrao: re.Pattern
    conta: str
    confianca: float
    premissa: bool = False
    observacao: str = ""

    def casa(self, banco: str, descricao: str) -> bool:
        return banco == self.banco and bool(self.padrao.search(descricao.upper()))


def _r(id_: str, banco: str, padrao: str, conta: str, confianca: float, premissa: bool = False, obs: str = "") -> Regra:
    return Regra(id_, banco, re.compile(padrao), conta, confianca, premissa, obs)


# A ordem importa: a primeira regra que casa vence. Mapeamento conferido nos extratos de setembro/2026.
REGRAS: tuple[Regra, ...] = (
    # ---------------------------------------------------------------- Aurora
    _r("A01_ORBE", "AURORA", r"^TED RECEBIDA .* ORBE", "1.1.03.001", 0.95, obs="Baixa o recebível da Orbe."),
    _r("A02_CONTABILIDADE", "AURORA", r"^PIX ENVIADO CONTABILIDADE", "4.2.06", 0.90,
       obs="Serviços contábeis: despesa direta do mês (não estava provisionada)."),
    _r("A03_REPASSE", "AURORA", r"^PIX ENVIADO ", "2.1.01.001", 0.90, obs="Repasse a lojista."),
    _r("A04_TRANSFERENCIA", "AURORA", r"^TRANSF ENTRE CONTAS", "1.1.09.001", 0.95,
       obs="Transferência entre contas próprias (conta transitória)."),
    _r("A05_FOLHA", "AURORA", r"^PAGTO SALARIOS", "2.1.04.001", 0.95, obs=PROVISAO),
    _r("A06_INSS", "AURORA", r"^GPS INSS", "2.1.04.002", 0.95, obs=PROVISAO),
    _r("A07_FGTS", "AURORA", r"^GRF FGTS", "2.1.04.003", 0.95, obs=PROVISAO),
    _r("A08_ISS", "AURORA", r"^PAGTO ISS", "2.1.03.003", 0.95, obs=PROVISAO),
    _r("A09_DARF_IRRF", "AURORA", r"^DEBITO DARF 0561", "2.1.03.004", 0.90,
       obs=PROVISAO + " Competência não declarada no extrato (pendência)."),
    _r("A10_DARF_PIS", "AURORA", r"^DEBITO DARF 8109", "2.1.03.001", 0.90,
       obs=PROVISAO + " Competência não declarada no extrato (pendência)."),
    _r("A11_DARF_COFINS", "AURORA", r"^DEBITO DARF 2172", "2.1.03.002", 0.90,
       obs=PROVISAO + " Competência não declarada no extrato (pendência)."),
    _r("A12_CONDOMINIO", "AURORA", r"^BOLETO CONDOMINIO", "4.2.02", 0.95, obs="Aluguel e condomínio: despesa do mês."),
    _r("A13_AWS", "AURORA", r"^DEB AUT AMAZON WEB SERVICES", "4.2.03", 0.95, obs="Cloud: despesa do mês."),
    _r("A14_GOOGLE", "AURORA", r"^CARTAO PJ - GOOGLE WORKSPACE", "4.2.04", 0.70, premissa=True,
       obs="PREMISSA: Google Workspace tratado como software e assinatura; o financeiro não confirmou."),
    _r("A15_TARIFA", "AURORA", r"^TAR ", "4.2.01", 0.95, obs="Tarifa bancária: despesa do mês."),
    _r("A16_PIX_SEM_ID", "AURORA", r"^PIX RECEBIDO .*SEM IDENTIFICACAO", "1.1.09.002", 0.90,
       obs="Não é receita até alguém identificar (Helena, financeiro). Pendência aberta."),
    _r("A17_DEVOLUCAO", "AURORA", r"^DEVOLUCAO PIX", "2.1.01.001", 0.70, premissa=True,
       obs="PREMISSA: PIX de repasse que voltou, então o repasse volta a ser devido. O financeiro aceita 2.1.01.001 ou "
           "2.1.01.002 desde que o critério seja o mesmo. Motivo da devolução desconhecido (pendência)."),
    # ---------------------------------------------------------------- Meridiano
    _r("M01_PIX_LOJISTA", "MERIDIANO", r"^PIX RECEB ", "2.1.02.001", 0.95,
       obs="Recursos de lojista para remessa a liquidar."),
    _r("M02_TED_PONTE", "MERIDIANO", r"^TED ENVIADA .*LIQ OPERACOES", "2.1.02.001", 0.95,
       obs="Liquidação de remessas: baixa os recursos de lojistas (Valor R$ + IOF das operações do dia)."),
    _r("M03_TRANSFERENCIA", "MERIDIANO", r"^TED RECEBIDA TARVO PAGAMENTOS LTDA - MESMA TITULARIDADE", "1.1.09.001", 0.95,
       obs="Transferência entre contas próprias (conta transitória)."),
    _r("M04_COMISSAO_PONTE", "MERIDIANO", r"^TED RECEB .*REPASSE COMISSAO", "1.1.03.002", 0.95,
       obs="Comissão de intermediação a receber: o spread de agosto já estava registrado (Helena, financeiro)."),
    _r("M05_CDB", "MERIDIANO", r"^(APLICACAO|RESGATE) AUTOMATIC[AO]", "1.1.02.001", 0.95,
       obs="Aplicação automática (CDB DI): aplicação ou resgate, sem efeito no resultado."),
    _r("M06_RENDIMENTO", "MERIDIANO", r"^RENDIMENTO APLIC", "3.2.01", 0.95, obs="Rendimento de aplicações: receita financeira."),
    _r("M07_TARIFA", "MERIDIANO", r"^TARIFA", "4.2.01", 0.95, obs="Tarifa bancária: despesa do mês."),
    _r("M08_SEGURO", "MERIDIANO", r"^SEGURO EMPRESARIAL", "4.2.05", 0.95, obs="Seguro: despesa do mês."),
    _r("M09_IOF", "MERIDIANO", r"^IOF S/ OPERACAO CREDITO", "4.3.01", 0.90,
       obs="IOF de operação de crédito: despesa financeira. A que operação se refere é pergunta em aberto."),
)

Sugestor = Callable[[dict], "tuple[str, float] | None"]


# ----------------------------------------------------------------------------- plano de contas
def ler_plano(caminho: Path) -> dict[str, dict]:
    texto, _ = ler_texto(caminho)
    return {r["cod_conta"]: r for r in csv.DictReader(io.StringIO(texto), delimiter=";")}


def contas_analiticas(plano: dict[str, dict]) -> set[str]:
    return {c for c, r in plano.items() if r["aceita_lancamento"] == "S"}


def checar_contas(contas: list[str], plano: dict[str, dict], onde: str = "classificação") -> None:
    """Falha se alguma conta não existir ou não aceitar lançamento (sintética)."""
    aceitas = contas_analiticas(plano)
    ruins = sorted({c for c in contas if c and c not in aceitas})
    if ruins:
        detalhe = ", ".join(f"{c} ({plano[c]['tipo'] if c in plano else 'inexistente'})" for c in ruins)
        raise ValueError(f"{onde}: conta que não aceita lançamento (ACEITA_LANCTO != S): {detalhe}")


# ----------------------------------------------------------------------------- classificação
def ler_banco(caminho: Path) -> list[dict]:
    texto, _ = ler_texto(caminho)
    return list(csv.DictReader(io.StringIO(texto), delimiter=";"))


def classificar(lancamentos: list[dict], plano: dict[str, dict], sugestor: Sugestor | None = None,
                regras: tuple[Regra, ...] = REGRAS) -> tuple[list[dict], list[dict], list[dict]]:
    """Devolve (linhas de lancamentos_classificados, linhas de rastro, lançamentos sem regra)."""
    checar_contas([r.conta for r in regras] + list(BANCO_CONTA.values()), plano, "regras da classificação")
    linhas, rastro, sem_regra = [], [], []
    for l in lancamentos:
        banco, desc = l["banco"], l["descricao"]
        valor = Decimal(l["valor"]).quantize(CENTAVO)
        regra = next((r for r in regras if r.casa(banco, desc)), None)
        if regra is not None:
            conta, metodo, conf, rid, premissa, obs = regra.conta, "REGRA", Decimal(str(regra.confianca)), regra.id, regra.premissa, regra.observacao
        else:
            sugestao = sugestor(l) if sugestor else None
            if sugestao and sugestao[0] in contas_analiticas(plano):
                conta, metodo, conf = sugestao[0], "IA", min(Decimal(str(sugestao[1])), Decimal("0.60"))
                rid, premissa, obs = "IA", True, "Sugestão de IA sem regra: confirmar com o financeiro."
            else:
                conta, metodo, conf, rid, premissa = "", "HUMANO", Decimal("0"), "SEM_REGRA", False
                obs = "Nenhuma regra casou com a descrição: classificar à mão."
                sem_regra.append(l)
        id_saida = f"LC-{l['competencia']}-{banco}-{l['ref_origem']}"
        linhas.append({
            "id_saida": id_saida, "banco": banco, "ref_origem": l["ref_origem"], "data": l["data"], "descricao": desc,
            "valor": valor, "conta_codigo": conta, "metodo": metodo, "confianca": conf.quantize(CENTAVO),
            "conta_descricao": plano[conta]["descricao"] if conta else "", "conta_banco": BANCO_CONTA[banco],
            "sentido": l["sentido"], "regra": rid, "premissa": "S" if premissa else "N", "observacao": obs,
        })
        rastro.append({"id_saida": id_saida, "arquivo_origem": l["arquivo_origem"], "ref_origem": l["ref_origem"],
                       "valor": valor})
    checar_contas([l["conta_codigo"] for l in linhas], plano)
    return linhas, rastro, sem_regra


# ----------------------------------------------------------------------------- conferência de saldos
def ler_controle(caminho: Path) -> list[dict]:
    texto, _ = ler_texto(caminho)
    return list(csv.DictReader(io.StringIO(texto), delimiter=";"))


def conferir_saldos(linhas: list[dict], controle: list[dict]) -> list[dict]:
    """Aurora: saldo anterior + soma dos lançamentos tem que dar o saldo final do extrato.
    Meridiano: o OFX só traz o saldo final, então não há como conferir a soma contra o saldo (devolve bate=None)."""
    def valor(fonte: str, item: str) -> Decimal | None:
        achado = [c["valor"] for c in controle if c["fonte"] == fonte and c["item"] == item]
        return Decimal(achado[0]) if achado else None

    saida = []
    for banco, fonte in (("AURORA", "aurora"), ("MERIDIANO", "meridiano")):
        soma = sum((l["valor"] for l in linhas if l["banco"] == banco), Decimal("0.00"))
        inicial, final = valor(fonte, "saldo_anterior"), valor(fonte, "saldo_final_informado")
        bate = None if inicial is None or final is None else (inicial + soma).quantize(CENTAVO) == final.quantize(CENTAVO)
        saida.append({"banco": banco, "lancamentos": sum(1 for l in linhas if l["banco"] == banco), "soma": soma,
                      "saldo_inicial": inicial, "saldo_final": final, "bate": bate})
    return saida


# ----------------------------------------------------------------------------- execução
def executar(mes: str, dados: Path, saida: Path | None) -> dict:
    dados = Path(dados)
    plano = ler_plano(dados / "dim_plano_contas.csv")
    banco = [l for l in ler_banco(dados / "fato_banco.csv") if l["competencia"] == mes]
    if not banco:
        raise ValueError(f"fato_banco.csv sem lançamentos da competência {mes}")
    linhas, rastro, sem_regra = classificar(banco, plano)
    saldos = conferir_saldos(linhas, ler_controle(dados / "controle_ingestao.csv"))
    if saida is not None:
        escrever_csv(Path(saida) / "lancamentos_classificados.csv", linhas, COL_LANCAMENTOS)
    return {"linhas": linhas, "rastro": rastro, "sem_regra": sem_regra, "saldos": saldos}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Classifica os lançamentos dos extratos no plano de contas.")
    ap.add_argument("--mes", default="2026-09")
    ap.add_argument("--dados", default="data", help="pasta com as tabelas da ingestão")
    ap.add_argument("--saida", default="saida", help="pasta onde gravar lancamentos_classificados.csv")
    a = ap.parse_args(argv)
    r = executar(a.mes, Path(a.dados), Path(a.saida))
    metodos: dict[str, int] = {}
    for l in r["linhas"]:
        metodos[l["metodo"]] = metodos.get(l["metodo"], 0) + 1
    print(f"{len(r['linhas'])} lançamentos classificados: {metodos}; sem regra: {len(r['sem_regra'])}")
    for s in r["saldos"]:
        veredito = {True: "BATE com o saldo do extrato", False: "NÃO BATE com o saldo do extrato",
                    None: "saldo inicial não consta no arquivo: não dá para conferir"}[s["bate"]]
        print(f"  {s['banco']}: soma {s['soma']} ({s['lancamentos']} lançamentos), {veredito}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
