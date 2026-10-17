"""Ingestão: transforma os arquivos brutos do data pack em tabelas padronizadas (CSV) na pasta de saída.

Uso (a partir da raiz do repositório):
    python -m src.ingestao --mes 2026-09 --entrada input --saida data

Todos os arquivos de entrada ficam em input/. Além dos 6 arquivos base (01 a 05b), qualquer outro arquivo no formato
da Orbe do mesmo mês (ex.: 06_orbe_ajustes_tardios_set2026.csv) entra em fato_orbe com seu arquivo e seu lote.

Gera 7 tabelas + 1 arquivo de controle:
    dim_lojista, dim_ec, dim_contrato_taxa, dim_plano_contas, fato_orbe, fato_ponte, fato_banco,
    controle_ingestao

Princípios:
  * Os arquivos são lidos como vêm. Nenhuma correção manual antes.
  * Nada é decidido por nome: a ligação EC -> lojista só existe se a tabela de taxas (ou
    config/mapeamento_ec.csv) disser. Sugestões por nome ficam em colunas separadas e nunca são usadas para juntar.
  * Toda linha gravada carrega arquivo_origem e linha_origem (rastro).
  * Nenhuma regra de comissão aqui. Isso é etapa seguinte.
"""
from __future__ import annotations

import argparse
import csv
import email
import io
import re
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN
from email import policy
from pathlib import Path

from .utils import (MESES, achar_arquivo, cnpj14, data_br, data_serial_excel, ec_texto, escrever_csv, ler_texto,
                    ler_xlsx, norm_cabecalho, norm_nome, num_br, num_ponto, pct_planilha, sha256, so_digitos)

# ----------------------------------------------------------------------------- esquemas das tabelas
COL_DIM_LOJISTA = ["lojista_id", "cnpj", "cnpj_ajustado", "nome_canonico", "nomes_alternativos", "ecs", "ativo",
                   "linha_checkout", "linha_remessa", "status_cadastro", "obs_tabela", "linha_planilha"]
COL_DIM_EC = ["ec", "status", "faturavel", "lojista_id", "cnpj", "nome_tabela", "nomes_orbe", "n_linhas_orbe",
              "visto_na_orbe", "fonte_mapeamento", "aprovado_por", "registrado_em", "sugestao_cnpj", "sugestao_nome_tabela",
              "observacao"]
COL_DIM_CONTRATO = ["lojista_id", "cnpj", "cnpj_ajustado", "ec", "ec_fonte", "nome_tabela", "vigencia_ini",
                    "vigencia_fim", "taxa_debito_pct", "taxa_credito_vista_pct", "taxa_credito_2_6x_pct",
                    "taxa_credito_7_12x_pct", "taxa_pix_pct", "taxa_antecipacao_pct", "spread_remessa_pct",
                    "spread_remessa_regra", "spread_remessa_efetivo_pct", "origem_condicao", "condicao_fonte",
                    "condicao_aprovada_por", "pct_em_texto", "obs", "comentario_celula", "linha_planilha"]
COL_DIM_PLANO = ["cod_conta", "descricao", "tipo", "natureza", "aceita_lancamento", "cod_superior", "nivel",
                 "dt_criacao"]
COL_FATO_ORBE = ["competencia", "arquivo_origem", "lote", "linha_origem", "id_transacao", "data_movimento", "ec",
                 "status_ec", "cnpj", "nome_estabelecimento", "tipo_lancamento", "modalidade", "faixa", "parcelas",
                 "bandeira", "valor_bruto", "taxa_aplicada_pct", "valor_taxa", "valor_liquido", "id_referencia",
                 "data_venda_original", "data_taxa_ref", "flag_ref_sem_origem", "flag_venda_mes_anterior"]
COL_FATO_PONTE = ["competencia", "arquivo_origem", "linha_origem", "num_op", "data_contratacao", "data_liquidacao",
                  "cnpj", "cnpj_ajustado", "cliente_nome", "moeda", "valor_me", "taxa_cliente", "ptax", "valor_brl",
                  "spread_brl", "spread_pct", "spread_estimado_brl", "iof_brl", "status_compliance", "observacao",
                  "flag_duplicata", "flag_spread_negativo", "flag_ressalva", "mes_contratacao",
                  "flag_liquidacao_mes_seguinte", "spread_contratado_pct", "flag_spread_diverge",
                  "flag_cnpj_fora_da_tabela"]
COL_FATO_BANCO = ["competencia", "banco", "ref_origem", "arquivo_origem", "linha_origem", "data", "descricao",
                  "documento", "valor", "sentido", "saldo", "tipo_lancamento", "contraparte", "contraparte_cnpj",
                  "competencia_declarada", "provisionado_antes"]
COL_CONTROLE = ["tipo", "fonte", "item", "valor", "detalhe"]

ORBE_COLUNAS = ["id_transacao", "data_movimento", "cod_estabelecimento", "nome_estabelecimento", "tipo_lancamento",
                "modalidade", "qtd_parcelas", "bandeira", "valor_bruto", "taxa_aplicada_pct", "valor_taxa",
                "valor_liquido", "id_referencia", "data_venda_original"]
PLANO_COLUNAS = ["COD_CONTA", "DESCRICAO", "TIPO", "NATUREZA", "ACEITA_LANCTO", "COD_SUPERIOR", "DT_CRIACAO"]


class Controle:
    """Acumula contagens e verificações. Cada linha vira uma linha de controle_ingestao.csv."""

    def __init__(self) -> None:
        self.linhas: list[dict] = []

    def add(self, tipo: str, fonte: str, item: str, valor, detalhe: str = "") -> None:
        self.linhas.append({"tipo": tipo, "fonte": fonte, "item": item, "valor": valor, "detalhe": detalhe})

    def verifica(self, fonte: str, item: str, ok: bool, detalhe: str = "") -> None:
        self.add("VERIFICACAO", fonte, item, "OK" if ok else "ALERTA", detalhe)


def dec_br(s: str) -> Decimal:
    return Decimal(str(s).replace(".", "").replace(",", "."))


# ----------------------------------------------------------------------------- leitura: Orbe
def ler_orbe(caminho: Path, ctl: Controle, lote: str = "BASE") -> list[dict]:
    """Lê um arquivo no formato do relatório da Orbe. Cada linha leva o arquivo e o lote de onde veio."""
    texto, enc = ler_texto(caminho)
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    faltando = [c for c in ORBE_COLUNAS if c not in (leitor.fieldnames or [])]
    if faltando:
        raise ValueError(f"{caminho.name} fora do contrato da Orbe: faltam colunas {faltando}")
    linhas = []
    for r in leitor:
        r = {k: (v or "").strip() for k, v in r.items()}
        r["_linha"] = leitor.line_num
        r["_arquivo"], r["_lote"] = caminho.name, lote
        linhas.append(r)
    ctl.add("ARQUIVO", "orbe", "arquivo", caminho.name, f"lote={lote}; encoding={enc}")
    ctl.add("ARQUIVO", "orbe", "sha256", sha256(caminho), caminho.name)
    ctl.add("CONTAGEM", "orbe", "linhas_lidas", len(linhas), f"{caminho.name} (lote {lote})")
    return linhas


def achar_complementos_orbe(entrada: Path, mes: str, base: Path) -> list[Path]:
    """Outros arquivos no formato da Orbe do mesmo mês (ex.: '06_orbe_ajustes_tardios_set2026.csv').
    Só entram os que trazem a marca do mês no nome, para não misturar meses que sobraram na pasta."""
    ano, m = mes.split("-")
    marca = f"{MESES[int(m) - 1]}{ano}"
    return sorted(p for p in Path(entrada).glob("[0-9][0-9]_orbe_*.csv")
                  if p.resolve() != base.resolve() and marca in p.name.lower())


def lote_do_arquivo(caminho: Path) -> str:
    return "TARDIO" if "tardio" in caminho.name.lower() else "COMPLEMENTO"


def ler_orbe_completo(base: Path, complementos: list[Path], ctl: Controle) -> list[dict]:
    """Base + complementos numa lista só. O Nº da transação tem que ser único entre todos os arquivos, e todo
    estorno ou reversão que chegou depois precisa apontar para uma linha que existe, de sinal oposto,
    do mesmo EC e com a mesma taxa."""
    linhas = ler_orbe(base, ctl, "BASE")
    for comp in complementos:
        linhas += ler_orbe(comp, ctl, lote_do_arquivo(comp))
    vistos: dict[str, dict] = {}
    for r in linhas:
        antes = vistos.get(r["id_transacao"])
        if antes is not None:
            raise ValueError(f"Nº de transação repetido entre arquivos: {r['id_transacao']} em "
                             f"{antes['_arquivo']} (linha {antes['_linha']}) e {r['_arquivo']} (linha {r['_linha']})")
        vistos[r["id_transacao"]] = r
    tardias = [r for r in linhas if r["_lote"] != "BASE"]
    if tardias:
        sem_origem, incoerentes = [], []
        for r in tardias:
            if not r["id_referencia"]:
                continue
            o = vistos.get(r["id_referencia"])
            if o is None:
                sem_origem.append(r["id_transacao"])
            elif not (dec_br(r["valor_bruto"]) == -dec_br(o["valor_bruto"]) and r["taxa_aplicada_pct"] == o["taxa_aplicada_pct"]
                      and r["cod_estabelecimento"] == o["cod_estabelecimento"]):
                incoerentes.append(r["id_transacao"])
        ctl.verifica("orbe", "ajustes_tardios_apontam_para_linha_existente", not sem_origem,
                     f"sem origem={sem_origem}" if sem_origem else f"{len(tardias)} linhas fora da base, todas com origem encontrada")
        ctl.verifica("orbe", "ajustes_tardios_com_valor_oposto_mesma_taxa_e_mesmo_ec", not incoerentes,
                     f"incoerentes={incoerentes}" if incoerentes else "valor oposto, mesma taxa e mesmo EC da linha original")
        refs = Counter(r["id_referencia"] for r in linhas if r["id_referencia"])
        repetidas = sorted(k for k, q in refs.items() if q > 1)
        ctl.verifica("orbe", "venda_estornada_ou_revertida_mais_de_uma_vez", not repetidas,
                     f"repetidas={repetidas}" if repetidas else "cada linha original é estornada ou revertida no máximo uma vez")
        for lote in sorted({r["_lote"] for r in tardias}):
            do_lote = [r for r in tardias if r["_lote"] == lote]
            liq = sum(dec_br(r["valor_liquido"]) for r in do_lote)
            ctl.add("CONTAGEM", "orbe", f"liquido_do_lote_{lote}", float(liq),
                    f"{len(do_lote)} linhas; efeito no líquido reportado ({', '.join(f'{t}={q}' for t, q in Counter(r['tipo_lancamento'] for r in do_lote).items())})")
    return linhas


def faixa_taxa(tipo: str, modalidade: str, parcelas: str) -> str:
    if "ANTECIPACAO" in tipo:
        return "antecipacao"
    q = int(parcelas) if parcelas.isdigit() else 0
    if modalidade == "DEBITO":
        return "debito"
    if modalidade == "PIX":
        return "pix"
    if modalidade == "CREDITO A VISTA":
        return "credito_a_vista"
    if modalidade == "CREDITO PARCELADO":
        return "credito_2_6x" if q <= 6 else "credito_7_12x"
    return "outro"


# ----------------------------------------------------------------------------- leitura: tabela de taxas
def parse_vigencia(texto: str) -> tuple[str, str]:
    """'até 14/09/2026' -> ('', '2026-09-14') ; 'a partir de 15/09/2026' / '01/01/2026' -> (data, '')."""
    t = (texto or "").strip()
    m = re.search(r"\d{2}/\d{2}/\d{4}", t)
    if not m:
        return "", ""
    d = data_br(m.group(0))
    if norm_cabecalho(t).startswith("ate"):
        return "", d
    return d, ""


def ler_tabela_taxas(caminho: Path, ctl: Controle) -> list[dict]:
    abas, comentarios = ler_xlsx(caminho)
    nome_aba = next((n for n in abas if norm_cabecalho(n).startswith("taxasvigentes")), None)
    if nome_aba is None:
        nome_aba = next((n for n in abas if "antigo" not in norm_cabecalho(n)), None)
    if nome_aba is None:
        raise ValueError("Tabela de taxas: nenhuma aba utilizável")
    cel = abas[nome_aba]
    linha_cab = next((r for (r, c), v in cel.items() if c == "A" and norm_cabecalho(v) == "lojista"), None)
    if linha_cab is None:
        raise ValueError("Tabela de taxas: cabeçalho 'Lojista' não encontrado")
    col_por_cab = {norm_cabecalho(v): c for (r, c), v in cel.items() if r == linha_cab}
    exigidas = ["lojista", "cnpj", "ecorbe", "debito", "creditoavista", "cred26x", "cred712x", "pix", "antecipacao",
                "spreadremessa", "vigencia", "obs"]
    ausentes = [e for e in exigidas if e not in col_por_cab]
    if ausentes:
        raise ValueError(f"Tabela de taxas fora do contrato: faltam colunas {ausentes}")
    coment: dict[int, list[str]] = defaultdict(list)
    for ref, txt in comentarios:
        coment[int(re.match(r"[A-Z]+(\d+)", ref).group(1))].append(txt.strip())

    contratos = []
    for r in sorted({r for (r, _c) in cel if r > linha_cab}):
        def g(k: str, r=r) -> str:
            return (cel.get((r, col_por_cab[k]), "") or "").strip()

        nome = g("lojista")
        if nome.startswith("*"):
            break
        if not nome:
            continue
        taxas_brutas = [g(k) for k in ("debito", "creditoavista", "cred26x", "cred712x", "pix", "antecipacao")]
        ini, fim = parse_vigencia(g("vigencia"))
        spread = pct_planilha(g("spreadremessa"))
        cnpj, ajustado = cnpj14(g("cnpj"))
        contratos.append({
            "nome_tabela": nome, "cnpj": cnpj, "cnpj_ajustado": ajustado, "ec": ec_texto(g("ecorbe")),
            "vigencia_ini": ini, "vigencia_fim": fim,
            "taxa_debito_pct": pct_planilha(taxas_brutas[0]), "taxa_credito_vista_pct": pct_planilha(taxas_brutas[1]),
            "taxa_credito_2_6x_pct": pct_planilha(taxas_brutas[2]),
            "taxa_credito_7_12x_pct": pct_planilha(taxas_brutas[3]), "taxa_pix_pct": pct_planilha(taxas_brutas[4]),
            "taxa_antecipacao_pct": pct_planilha(taxas_brutas[5]),
            "spread_remessa_pct": spread, "spread_remessa_regra": "EXPLICITO" if spread is not None else "PADRAO",
            "pct_em_texto": any("%" in t for t in taxas_brutas), "obs": g("obs"),
            "comentario_celula": " | ".join(coment.get(r, [])), "linha_planilha": r,
            "ec_fonte": "TABELA" if ec_texto(g("ecorbe")) else "", "origem_condicao": "TABELA",
            "condicao_fonte": "", "condicao_aprovada_por": "",
        })
    ctl.add("ARQUIVO", "tabela_taxas", "arquivo", caminho.name, f"aba={nome_aba}; abas ignoradas="
            f"{[n for n in abas if n != nome_aba]}")
    ctl.add("ARQUIVO", "tabela_taxas", "sha256", sha256(caminho))
    ctl.add("CONTAGEM", "tabela_taxas", "linhas_lidas", len(contratos))
    ctl.add("CONTAGEM", "tabela_taxas", "comentarios_de_celula", len(comentarios))
    return contratos


# ----------------------------------------------------------------------------- leitura: Ponte
PONTE_MAPA = {"nooperacao": "num_op", "datacontratacao": "data_contratacao", "dataliquidacao": "data_liquidacao",
              "cnpjcliente": "cnpj", "cliente": "cliente", "moeda": "moeda", "valorme": "valor_me",
              "taxacliente": "taxa_cliente", "ptaxref": "ptax", "valorr": "valor_brl", "spreadr": "spread_brl",
              "spread": "spread_pct", "spreadestimadord1": "spread_estimado_brl", "iofr": "iof_brl",
              "statuscompliance": "status", "observacao": "obs"}


def ler_ponte(caminho: Path, ctl: Controle) -> tuple[list[dict], str]:
    msg = email.message_from_bytes(caminho.read_bytes(), policy=policy.default)
    anexos = [(p.get_filename(), p.get_content()) for p in msg.iter_attachments()
              if (p.get_filename() or "").lower().endswith(".xlsx")]
    if not anexos:
        raise ValueError("E-mail da Ponte sem anexo .xlsx")
    nome_anexo, conteudo = anexos[0]
    abas, _ = ler_xlsx(conteudo)
    nome_aba = next((n for n in abas if norm_cabecalho(n).startswith("operac")), None)
    if nome_aba is None:
        raise ValueError("Relatório da Ponte: aba de operações não encontrada")
    cel = abas[nome_aba]
    linha_cab = next((r for (r, c), v in cel.items()
                      if c == "A" and "operacao" in norm_cabecalho(v) and norm_cabecalho(v).startswith("n")), None)
    if linha_cab is None:
        raise ValueError("Relatório da Ponte: cabeçalho 'Nº Operação' não encontrado")
    col_por_campo = {}
    for (r, c), v in cel.items():
        if r == linha_cab and norm_cabecalho(v) in PONTE_MAPA:
            col_por_campo[PONTE_MAPA[norm_cabecalho(v)]] = c
    faltando = sorted(set(PONTE_MAPA.values()) - set(col_por_campo))
    if faltando:
        raise ValueError(f"Relatório da Ponte fora do contrato: faltam colunas {faltando}")

    ops, totais = [], {}
    for r in sorted({r for (r, _c) in cel if r > linha_cab}):
        a = (cel.get((r, "A"), "") or "").strip()
        if re.fullmatch(r"PC-\d{4}-\d+", a):
            ops.append({"_linha": r, **{k: (cel.get((r, c), "") or "").strip() for k, c in col_por_campo.items()}})
        elif norm_cabecalho(a).startswith("totaldeoperacoes"):
            totais["ops"] = num_ponto(cel.get((r, "B"), ""))
        elif norm_cabecalho(a).startswith("spreadtotal"):
            totais["spread"] = num_ponto(cel.get((r, "B"), ""))
    ctl.add("ARQUIVO", "ponte", "arquivo", caminho.name, f"anexo={nome_anexo}; aba={nome_aba}")
    ctl.add("ARQUIVO", "ponte", "sha256", sha256(caminho))
    try:
        ctl.add("ARQUIVO", "ponte", "data_email", email.utils.parsedate_to_datetime(msg["Date"]).date().isoformat(),
                "cabeçalho Date do e-mail; o prazo de contestação da Ponte conta a partir dele")
    except (TypeError, ValueError):
        pass          # e-mail sem Date legível: o prazo fica sem data
    ctl.add("CONTAGEM", "ponte", "linhas_lidas", len(ops))
    if "ops" in totais:
        ctl.add("CONTAGEM", "ponte", "total_declarado_operacoes", totais["ops"])
    if "spread" in totais:
        ctl.add("CONTAGEM", "ponte", "total_declarado_spread_brl", totais["spread"])
    return ops, f"{caminho.name}::{nome_anexo}"


# ----------------------------------------------------------------------------- leitura: plano de contas
def ler_plano(caminho: Path, ctl: Controle) -> list[dict]:
    texto, enc = ler_texto(caminho)
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    faltando = [c for c in PLANO_COLUNAS if c not in (leitor.fieldnames or [])]
    if faltando:
        raise ValueError(f"Plano de contas fora do contrato: faltam colunas {faltando}")
    contas = []
    for r in leitor:
        r = {k: (v or "").strip() for k, v in r.items()}
        if not r["COD_CONTA"]:
            continue
        contas.append({
            "cod_conta": r["COD_CONTA"], "descricao": r["DESCRICAO"], "tipo": r["TIPO"], "natureza": r["NATUREZA"],
            "aceita_lancamento": r["ACEITA_LANCTO"], "cod_superior": r["COD_SUPERIOR"],
            "nivel": r["COD_CONTA"].count(".") + 1, "dt_criacao": data_br(r["DT_CRIACAO"]),
        })
    ctl.add("ARQUIVO", "plano_contas", "arquivo", caminho.name, f"encoding={enc}")
    ctl.add("ARQUIVO", "plano_contas", "sha256", sha256(caminho))
    ctl.add("CONTAGEM", "plano_contas", "linhas_lidas", len(contas))
    return contas


# ----------------------------------------------------------------------------- leitura: bancos
PADRAO_TIPO = re.compile(r"[A-Za-zÀ-ÿ]+(?: [A-Za-zÀ-ÿ]+)?")


def tipo_lancamento(desc: str) -> str:
    m = PADRAO_TIPO.match(desc.strip())
    return m.group(0).upper() if m else ""


def extrair_contraparte(desc: str) -> tuple[str, str]:
    """Extrai (contraparte, cnpj) da descrição quando a forma é conhecida. Não classifica, só separa o nome."""
    d = desc.strip()
    padroes = [
        (r"^TED RECEBIDA (\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}) (.+)$", lambda m: (m.group(2), m.group(1))),
        (r"^PIX RECEBIDO (\d{14}) SEM IDENTIFICACAO$", lambda m: ("SEM IDENTIFICACAO", m.group(1))),
        (r"^PIX ENVIADO (.+)$", lambda m: (m.group(1), "")),
        (r"^PIX RECEB (.+)$", lambda m: (m.group(1), "")),
        (r"^DEVOLUCAO PIX - (.+)$", lambda m: (m.group(1), "")),
        (r"^TRANSF ENTRE CONTAS P/ BCO (\w+)", lambda m: (f"TARVO (MESMA TITULARIDADE) {m.group(1)}", "")),
        (r"^TED RECEBIDA TARVO PAGAMENTOS LTDA - MESMA TITULARIDADE$",
         lambda m: ("TARVO (MESMA TITULARIDADE)", "")),
        (r"^TED ENVIADA (.+?) LIQ OPERACOES$", lambda m: (m.group(1), "")),
        (r"^TED RECEB (.+?) REPASSE COMISSAO", lambda m: (m.group(1), "")),
    ]
    for p, f in padroes:
        m = re.match(p, d)
        if m:
            nome, cnpj = f(m)
            return nome.strip(), so_digitos(cnpj)
    return "", ""


def ler_aurora(caminho: Path, competencia: str, ctl: Controle) -> list[dict]:
    texto, enc = ler_texto(caminho)
    linhas = texto.replace("\r\n", "\n").split("\n")
    cab = next((i for i, l in enumerate(linhas) if l.startswith("Data;")), None)
    if cab is None:
        raise ValueError("Aurora: cabeçalho 'Data;Lançamento;...' não encontrado")
    registros, saldo_ini, saldo_fim = [], None, None
    for i in range(cab + 1, len(linhas)):
        p = linhas[i].split(";")
        p += [""] * (5 - len(p))
        data, desc, doc, valor, saldo = (x.strip() for x in p[:5])
        if desc == "SALDO ANTERIOR":
            saldo_ini = num_br(saldo)
            continue
        if desc == "SALDO FINAL":
            saldo_fim = num_br(saldo)
            continue
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
            continue
        v = num_br(valor)
        contra, cnpj = extrair_contraparte(desc)
        registros.append({
            "competencia": competencia, "banco": "AURORA", "ref_origem": f"L{i + 1}", "arquivo_origem": caminho.name,
            "linha_origem": i + 1, "data": data_br(data), "descricao": desc, "documento": doc, "valor": v,
            "sentido": "ENTRADA" if v is not None and v > 0 else "SAIDA", "saldo": num_br(saldo),
            "tipo_lancamento": tipo_lancamento(desc), "contraparte": contra, "contraparte_cnpj": cnpj,
        })
    ctl.add("ARQUIVO", "aurora", "arquivo", caminho.name, f"encoding={enc}")
    ctl.add("ARQUIVO", "aurora", "sha256", sha256(caminho))
    ctl.add("CONTAGEM", "aurora", "linhas_lidas", len(registros))
    if saldo_ini is not None:
        ctl.add("CONTAGEM", "aurora", "saldo_anterior", saldo_ini)
    if saldo_fim is not None:
        ctl.add("CONTAGEM", "aurora", "saldo_final_informado", saldo_fim)
    if saldo_ini is not None and saldo_fim is not None:
        calc = round(saldo_ini + sum(r["valor"] for r in registros), 2)
        ctl.verifica("aurora", "saldo_final_recalculado_igual_ao_informado", abs(calc - saldo_fim) < 0.005,
                     f"calculado={calc}; informado={saldo_fim}")
        corrente, quebras = saldo_ini, 0
        for r in registros:
            corrente = round(corrente + r["valor"], 2)
            if r["saldo"] is None or abs(corrente - r["saldo"]) > 0.005:
                quebras += 1
        ctl.verifica("aurora", "saldo_linha_a_linha_confere", quebras == 0, f"linhas_com_diferenca={quebras}")
    return registros


def ler_meridiano(caminho: Path, competencia: str, ctl: Controle) -> list[dict]:
    texto, enc = ler_texto(caminho)
    registros = []
    for m in re.finditer(r"<STMTTRN>(.*?)</STMTTRN>", texto, flags=re.S):
        campos = dict(re.findall(r"<(\w+)>([^\r\n<]*)", m.group(1)))
        valor = num_ponto(campos.get("TRNAMT", ""))
        desc = (campos.get("MEMO") or "").strip()
        contra, cnpj = extrair_contraparte(desc)
        dt = campos.get("DTPOSTED", "")[:8]
        registros.append({
            "competencia": competencia, "banco": "MERIDIANO", "ref_origem": campos.get("FITID", ""),
            "arquivo_origem": caminho.name, "linha_origem": texto.count("\n", 0, m.start()) + 1,
            "data": f"{dt[:4]}-{dt[4:6]}-{dt[6:8]}" if len(dt) == 8 else "", "descricao": desc,
            "documento": campos.get("CHECKNUM", ""), "valor": valor,
            "sentido": "ENTRADA" if valor is not None and valor > 0 else "SAIDA", "saldo": None,
            "tipo_lancamento": tipo_lancamento(desc), "contraparte": contra, "contraparte_cnpj": cnpj,
        })
    bal = re.search(r"<LEDGERBAL>\s*<BALAMT>([-\d.]+)", texto)
    ctl.add("ARQUIVO", "meridiano", "arquivo", caminho.name, f"encoding={enc}")
    ctl.add("ARQUIVO", "meridiano", "sha256", sha256(caminho))
    ctl.add("CONTAGEM", "meridiano", "linhas_lidas", len(registros))
    if bal:
        ctl.add("CONTAGEM", "meridiano", "saldo_final_informado", num_ponto(bal.group(1)),
                "o OFX não traz saldo inicial; não dá para recalcular")
    ids = [r["ref_origem"] for r in registros]
    ctl.verifica("meridiano", "fitid_unico", len(ids) == len(set(ids)), f"duplicados={len(ids) - len(set(ids))}")
    return registros


# ----------------------------------------------------------------------------- construção das dimensões
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
TAXAS_COLS = ["taxa_debito_pct", "taxa_credito_vista_pct", "taxa_credito_2_6x_pct", "taxa_credito_7_12x_pct",
              "taxa_pix_pct", "taxa_antecipacao_pct"]


def ler_config(nome: str) -> list[dict]:
    """Lê um CSV de config/ (decisões confirmadas pelo financeiro, com fonte e quem aprovou)."""
    caminho = CONFIG_DIR / nome
    if not caminho.exists():
        return []
    texto, _ = ler_texto(caminho)
    linhas = []
    for r in csv.DictReader(io.StringIO(texto), delimiter=";"):
        if None in r:
            raise ValueError(f"config/{nome}: linha com campos a mais (algum texto tem ';'): {list(r.values())[:2]}")
        linhas.append({k: (v or "").strip() for k, v in r.items()})
    return linhas


def ler_overrides() -> dict[str, dict]:
    return {ec_texto(r["ec"]): r for r in ler_config("mapeamento_ec.csv") if r.get("ec")}


def ler_parametros() -> dict[str, float]:
    params = {r["chave"]: float(r["valor"].replace(",", ".")) for r in ler_config("parametros.csv") if r.get("chave")}
    for obrigatorio in ("spread_padrao_pct", "tolerancia_spread_pp"):
        if obrigatorio not in params:
            raise ValueError(f"config/parametros.csv sem a chave obrigatória '{obrigatorio}'")
    return params


def dia_vizinho(iso: str, delta: int) -> str:
    return (date.fromisoformat(iso) + timedelta(days=delta)).isoformat()


def vincular_ecs(contratos: list[dict], overrides: dict[str, dict]) -> int:
    """EC confirmado pelo financeiro: preenche o EC nas linhas da tabela que têm o mesmo CNPJ e estão sem EC."""
    n = 0
    for ec, ov in overrides.items():
        if ov.get("status", "").upper() != "CONFIRMADO" or not ov.get("cnpj"):
            continue
        cnpj = cnpj14(ov["cnpj"])[0]
        for c in contratos:
            if c["cnpj"] == cnpj and not c["ec"]:
                c["ec"], c["ec_fonte"] = ec, "CONFIRMADO_FINANCEIRO"
                n += 1
    return n


def aplicar_condicoes(contratos: list[dict], condicoes: list[dict], ctl: Controle) -> list[dict]:
    """Condição comercial com vigência (ex.: tarifa zerada de set a dez) vira uma linha nova em dim_contrato_taxa.
    A linha base é encerrada na véspera e, se a condição tem fim, a base é retomada no dia seguinte."""
    saida = list(contratos)
    for cond in condicoes:
        cnpj = cnpj14(cond["cnpj"])[0]
        ini, fim = cond["vigencia_ini"], cond["vigencia_fim"]
        vigentes = [c for c in saida if c["cnpj"] == cnpj
                    and (not c["vigencia_ini"] or c["vigencia_ini"] <= ini)
                    and (not c["vigencia_fim"] or c["vigencia_fim"] >= ini)]
        if not vigentes:
            ctl.verifica("condicoes_comerciais", f"{cnpj}_tem_linha_base_em_{ini}", False,
                         "nenhuma linha de contrato vigente nessa data; condição ignorada")
            continue
        base = vigentes[-1]
        fim_base = base["vigencia_fim"]
        nova = dict(base)
        for col in TAXAS_COLS + ["spread_remessa_pct"]:
            if cond.get(col, "") != "":
                nova[col] = float(cond[col].replace(",", "."))
        nova.update(vigencia_ini=ini, vigencia_fim=fim, origem_condicao="CONFIG",
                    condicao_fonte=cond.get("fonte", ""), condicao_aprovada_por=cond.get("aprovado_por", ""))
        if nova["spread_remessa_pct"] is not None:
            nova["spread_remessa_regra"] = "EXPLICITO"
        retomada = None
        if fim and (not fim_base or fim_base > fim):
            retomada = dict(base)
            retomada.update(vigencia_ini=dia_vizinho(fim, 1), vigencia_fim=fim_base, origem_condicao="TABELA (retomada)")
        base["vigencia_fim"] = dia_vizinho(ini, -1)
        saida.append(nova)
        if retomada:
            saida.append(retomada)
        ctl.add("REGRA", "condicoes_comerciais", f"{cnpj} de {ini} a {fim or 'sem fim'}",
                ", ".join(f"{c}={nova[c]}" for c in TAXAS_COLS if cond.get(c, "") != ""),
                f"{cond.get('fonte', '')} | aprovado por {cond.get('aprovado_por', '')} em {cond.get('registrado_em', '')}")
    return saida


def contem_nome(a: str, b: str) -> bool:
    """True se um nome normalizado contém o outro com pelo menos 2 palavras. Só para SUGESTÃO."""
    if len(a.split()) < 2 or len(b.split()) < 2:
        return False
    return a in b or b in a


def construir_dim_ec(orbe: list[dict], contratos: list[dict], overrides: dict[str, dict]) -> list[dict]:
    nomes: dict[str, set] = defaultdict(set)
    n_linhas: Counter = Counter()
    for r in orbe:
        ec = ec_texto(r["cod_estabelecimento"])
        nomes[ec].add(r["nome_estabelecimento"])
        n_linhas[ec] += 1
    contratos_por_ec: dict[str, list[dict]] = defaultdict(list)
    for c in contratos:
        if c["ec"]:
            contratos_por_ec[c["ec"]].append(c)
    sem_ec = [c for c in contratos if not c["ec"]]

    # A dimensão é a UNIÃO de tudo o que se sabe sobre ECs: vistos na Orbe do mês, presentes na tabela de taxas e
    # citados em config/mapeamento_ec.csv. Um EC confirmado não some só porque não vendeu no mês.
    universo = set(n_linhas) | set(contratos_por_ec) | set(overrides)

    linhas = []
    for ec in sorted(universo):
        ov = overrides.get(ec)
        sugestao_cnpj, sugestao_nome, obs, aprovado, registrado = "", "", "", "", ""
        if ov and ov.get("status"):
            status, cnpj, fonte = ov["status"].upper(), cnpj14(ov.get("cnpj", ""))[0], "config/mapeamento_ec.csv"
            obs, aprovado, registrado = ov.get("fonte", ""), ov.get("aprovado_por", ""), ov.get("registrado_em", "")
        elif ec in contratos_por_ec:
            status, cnpj, fonte = "CONFIRMADO", contratos_por_ec[ec][0]["cnpj"], "tabela_taxas"
        else:
            status, cnpj, fonte = "PENDENTE", "", ""
            obs = "EC sem mapeamento confirmado; aguardando o financeiro"
        if status != "CONFIRMADO":
            cands = {}
            for c in sem_ec:
                if any(contem_nome(norm_nome(n), norm_nome(c["nome_tabela"])) for n in nomes[ec]):
                    cands[c["cnpj"]] = c["nome_tabela"]
            if len(cands) == 1:
                sugestao_cnpj, sugestao_nome = next(iter(cands.items()))
                obs = (obs + "; " if obs else "") + "sugestao por nome, NAO confirmada, nao usada em joins"
        nome_tabela = contratos_por_ec[ec][0]["nome_tabela"] if ec in contratos_por_ec else ""
        texto_tabela = " ".join(f"{c['obs']} {c['comentario_celula']}" for c in contratos_por_ec.get(ec, []))
        inativo = "inativo" in norm_cabecalho(texto_tabela)
        if inativo:
            obs = (obs + "; " if obs else "") + "lojista inativo na planilha"
        linhas.append({
            "ec": ec, "status": status, "faturavel": status == "CONFIRMADO" and not inativo, "lojista_id": "",
            "cnpj": cnpj, "nome_tabela": nome_tabela, "nomes_orbe": " | ".join(sorted(nomes[ec])),
            "n_linhas_orbe": n_linhas[ec], "visto_na_orbe": n_linhas[ec] > 0,
            "fonte_mapeamento": fonte, "aprovado_por": aprovado, "registrado_em": registrado,
            "sugestao_cnpj": sugestao_cnpj, "sugestao_nome_tabela": sugestao_nome, "observacao": obs,
        })
    for l in linhas:
        l["lojista_id"] = l["cnpj"] if l["cnpj"] else f"EC{l['ec']}"
    return linhas


# ECs que o financeiro respondeu no canal #tarvo-financeiro e o status que cada um TEM que ter na dim_ec.
# A decisão em si (CNPJ, quem aprovou) vive em config/mapeamento_ec.csv; aqui fica só o contrato de integridade.
# Se a config perder um desses ECs, a ingestão para em vez de seguir com dado errado.
ECS_RESPONDIDOS_PELO_FINANCEIRO = {
    "1043300981": "CONFIRMADO",   # Novo Horizonte Intercâmbio
    "1043396662": "CONFIRMADO",   # Horizonte Viagens e Turismo (empresa diferente da Novo Horizonte)
    "1038867654": "CONFIRMADO",   # Kiwi Experience
    "1076801732": "RETIDO",       # Atlas Idiomas: não faturar até o comercial confirmar a taxa
}


def checar_integridade_dim_ec(dim_ec: list[dict], orbe: list[dict], contratos: list[dict],
                              overrides: dict[str, dict], ctl: Controle) -> None:
    """Para a ingestão (ValueError) se a dim_ec estiver incompleta ou contradisser o que o financeiro respondeu."""
    por_ec = {e["ec"]: e for e in dim_ec}
    erros = []
    if len(por_ec) != len(dim_ec):
        erros.append("EC repetido na dim_ec")
    universo = ({ec_texto(r["cod_estabelecimento"]) for r in orbe} | {c["ec"] for c in contratos if c["ec"]}
                | set(overrides))
    faltam = sorted(universo - set(por_ec))
    if faltam:
        erros.append(f"ECs conhecidos que não entraram na dim_ec: {faltam}")
    for ec, esperado in ECS_RESPONDIDOS_PELO_FINANCEIRO.items():
        atual = por_ec.get(ec, {}).get("status")
        if atual != esperado:
            erros.append(f"EC {ec}: esperado {esperado}, encontrado {atual}")
        elif esperado == "CONFIRMADO" and not por_ec[ec]["cnpj"]:
            erros.append(f"EC {ec} CONFIRMADO sem CNPJ")
    ctl.verifica("dim_ec", "dim_ec_cobre_orbe_tabela_e_config", not faltam,
                 f"ECs no universo={len(universo)}; na dim_ec={len(por_ec)}")
    ctl.verifica("dim_ec", "ecs_respondidos_pelo_financeiro_com_status_esperado",
                 all(por_ec.get(ec, {}).get("status") == s for ec, s in ECS_RESPONDIDOS_PELO_FINANCEIRO.items()),
                 ", ".join(f"{ec}={s}" for ec, s in ECS_RESPONDIDOS_PELO_FINANCEIRO.items()))
    ctl.add("CONTAGEM", "dim_ec", "ecs_so_na_tabela_ou_config_sem_venda_no_mes",
            sum(1 for e in dim_ec if not e["visto_na_orbe"]),
            ", ".join(f"{e['ec']} ({e['nome_tabela'] or 'sem nome'})" for e in dim_ec if not e["visto_na_orbe"]))
    if erros:
        raise ValueError("Integridade da dim_ec violada: " + "; ".join(erros))


def construir_dim_lojista(contratos: list[dict], dim_ec: list[dict], ponte: list[dict]) -> list[dict]:
    ecs_por_cnpj: dict[str, list[str]] = defaultdict(list)
    nomes_orbe_por_cnpj: dict[str, set] = defaultdict(set)
    for e in dim_ec:
        if e["status"] == "CONFIRMADO" and e["cnpj"]:
            ecs_por_cnpj[e["cnpj"]].append(e["ec"])
            nomes_orbe_por_cnpj[e["cnpj"]].update(n for n in e["nomes_orbe"].split(" | ") if n)
    nomes_ponte: dict[str, set] = defaultdict(set)
    for o in ponte:
        nomes_ponte[cnpj14(o["cnpj"])[0]].add(o["cliente"])

    por_cnpj: dict[str, list[dict]] = defaultdict(list)
    for c in contratos:
        por_cnpj[c["cnpj"]].append(c)

    linhas = []
    for cnpj, rows in por_cnpj.items():
        principal = rows[0]
        nomes_alt = {r["nome_tabela"] for r in rows[1:]} | nomes_orbe_por_cnpj.get(cnpj, set()) | nomes_ponte.get(cnpj, set())
        nomes_alt.discard(principal["nome_tabela"])
        texto_obs = " ".join(f"{r['obs']} {r['comentario_celula']}" for r in rows)
        tem_taxa = any(r[k] is not None for r in rows for k in
                       ("taxa_debito_pct", "taxa_credito_vista_pct", "taxa_credito_2_6x_pct", "taxa_credito_7_12x_pct",
                        "taxa_pix_pct"))
        remessa = (any(r["spread_remessa_pct"] is not None for r in rows) or cnpj in nomes_ponte
                   or "remessa" in norm_cabecalho(texto_obs))
        linhas.append({
            "lojista_id": cnpj, "cnpj": cnpj, "cnpj_ajustado": any(r["cnpj_ajustado"] for r in rows),
            "nome_canonico": principal["nome_tabela"], "nomes_alternativos": " | ".join(sorted(nomes_alt)),
            "ecs": " | ".join(sorted(ecs_por_cnpj.get(cnpj, []))),
            "ativo": "inativo" not in norm_cabecalho(texto_obs), "linha_checkout": bool(tem_taxa or ecs_por_cnpj.get(cnpj)),
            "linha_remessa": remessa, "status_cadastro": "NA_TABELA",
            "obs_tabela": " | ".join(sorted(x for x in {r["obs"] for r in rows} if x)),
            "linha_planilha": " | ".join(str(n) for n in sorted({r["linha_planilha"] for r in rows})),
        })
    for e in dim_ec:
        if not e["cnpj"] and e["status"] == "RETIDO":
            linhas.append({
                "lojista_id": e["lojista_id"], "cnpj": "", "cnpj_ajustado": False, "nome_canonico": e["nomes_orbe"],
                "nomes_alternativos": "", "ecs": e["ec"], "ativo": True, "linha_checkout": True,
                "linha_remessa": False, "status_cadastro": "SEM_CADASTRO_NA_TABELA", "obs_tabela": e["observacao"],
                "linha_planilha": "",
            })
    return linhas


# ----------------------------------------------------------------------------- construção dos fatos
def construir_fato_orbe(orbe: list[dict], dim_ec: list[dict], competencia: str, ctl: Controle) -> list[dict]:
    ec_info = {e["ec"]: e for e in dim_ec}
    ids = {r["id_transacao"] for r in orbe}
    inicio = f"{competencia}-01"
    linhas, falha_aritmetica, falha_liquido = [], 0, 0
    for r in orbe:
        ec = ec_texto(r["cod_estabelecimento"])
        bruto, taxa_pct = dec_br(r["valor_bruto"]), dec_br(r["taxa_aplicada_pct"])
        v_taxa, v_liq = dec_br(r["valor_taxa"]), dec_br(r["valor_liquido"])
        if (bruto * taxa_pct / Decimal(100)).quantize(Decimal("0.01"), ROUND_DOWN) != v_taxa:
            falha_aritmetica += 1
        if bruto - v_taxa != v_liq:
            falha_liquido += 1
        venda_orig = data_br(r["data_venda_original"])
        data_mov = data_br(r["data_movimento"])
        linhas.append({
            "competencia": competencia, "arquivo_origem": r["_arquivo"], "lote": r["_lote"], "linha_origem": r["_linha"],
            "id_transacao": r["id_transacao"], "data_movimento": data_mov, "ec": ec,
            "status_ec": ec_info[ec]["status"], "cnpj": ec_info[ec]["cnpj"] if ec_info[ec]["status"] == "CONFIRMADO" else "",
            "nome_estabelecimento": r["nome_estabelecimento"], "tipo_lancamento": r["tipo_lancamento"],
            "modalidade": r["modalidade"], "faixa": faixa_taxa(r["tipo_lancamento"], r["modalidade"], r["qtd_parcelas"]),
            "parcelas": int(r["qtd_parcelas"]) if r["qtd_parcelas"].isdigit() else None, "bandeira": r["bandeira"],
            "valor_bruto": round(float(bruto), 2), "taxa_aplicada_pct": round(float(taxa_pct), 4),
            "valor_taxa": round(float(v_taxa), 2), "valor_liquido": round(float(v_liq), 2),
            "id_referencia": r["id_referencia"], "data_venda_original": venda_orig,
            "data_taxa_ref": venda_orig or data_mov,
            "flag_ref_sem_origem": bool(r["id_referencia"]) and r["id_referencia"] not in ids,
            "flag_venda_mes_anterior": bool(venda_orig) and venda_orig < inicio,
        })
    n_dup = len(orbe) - len(ids)
    ctl.verifica("orbe", "id_transacao_unico", n_dup == 0, f"duplicados={n_dup}")
    ctl.verifica("orbe", "valor_taxa_igual_bruto_x_taxa_truncado", falha_aritmetica == 0,
                 f"linhas_com_diferenca={falha_aritmetica} (a Orbe trunca em centavos)")
    ctl.verifica("orbe", "liquido_igual_bruto_menos_taxa", falha_liquido == 0, f"linhas_com_diferenca={falha_liquido}")
    ctl.add("CONTAGEM", "orbe", "estornos_sem_venda_original_no_arquivo",
            sum(1 for l in linhas if l["tipo_lancamento"] == "ESTORNO" and l["flag_ref_sem_origem"]))
    ctl.add("CONTAGEM", "orbe", "linhas_em_ec_nao_confirmado", sum(1 for l in linhas if l["status_ec"] != "CONFIRMADO"))
    return linhas


def construir_fato_ponte(ops: list[dict], arquivo: str, competencia: str, contratos: list[dict],
                         params: dict[str, float], ctl: Controle) -> list[dict]:
    vistos: Counter = Counter()
    linhas = []
    cnpjs_tabela = {c["cnpj"] for c in contratos}

    def spread_contratado(cnpj: str, data: str) -> float | None:
        """Spread contratado (ou o padrão, se a célula está em branco) vigente na data de contratação."""
        rows = [c for c in contratos if c["cnpj"] == cnpj]
        if not rows:
            return None
        vig = [c for c in rows if (not c["vigencia_ini"] or c["vigencia_ini"] <= data)
               and (not c["vigencia_fim"] or c["vigencia_fim"] >= data)]
        return (vig or rows)[0]["spread_remessa_efetivo_pct"]

    for o in ops:
        vistos[o["num_op"]] += 1
        cnpj, ajustado = cnpj14(o["cnpj"])
        spread = num_ponto(o["spread_brl"])
        frac = num_ponto(o["spread_pct"])
        d_contr, d_liq = data_serial_excel(o["data_contratacao"]), data_serial_excel(o["data_liquidacao"])
        pct = None if frac is None else round(frac * 100, 4)
        contratado = spread_contratado(cnpj, d_contr)
        linhas.append({
            "mes_contratacao": d_contr[:7], "flag_liquidacao_mes_seguinte": d_liq[:7] != d_contr[:7],
            "spread_contratado_pct": contratado,
            "flag_spread_diverge": (contratado is not None and pct is not None
                                    and abs(pct - contratado) > params["tolerancia_spread_pp"]),
            "flag_cnpj_fora_da_tabela": cnpj not in cnpjs_tabela,
            "competencia": competencia, "arquivo_origem": arquivo, "linha_origem": o["_linha"],
            "num_op": o["num_op"], "data_contratacao": d_contr,
            "data_liquidacao": d_liq, "cnpj": cnpj, "cnpj_ajustado": ajustado,
            "cliente_nome": o["cliente"], "moeda": o["moeda"], "valor_me": round(num_ponto(o["valor_me"]), 2),
            "taxa_cliente": round(num_ponto(o["taxa_cliente"]), 6), "ptax": round(num_ponto(o["ptax"]), 6),
            "valor_brl": round(num_ponto(o["valor_brl"]), 2), "spread_brl": round(spread, 2),
            "spread_pct": None if frac is None else round(frac * 100, 4),
            "spread_estimado_brl": round(num_ponto(o["spread_estimado_brl"]), 2),
            "iof_brl": round(num_ponto(o["iof_brl"]), 2), "status_compliance": o["status"], "observacao": o["obs"],
            "flag_duplicata": vistos[o["num_op"]] > 1, "flag_spread_negativo": spread < 0,
            "flag_ressalva": "RESSALVA" in o["status"].upper(),
        })
    por_num = Counter(l["num_op"] for l in linhas)
    ctl.add("CONTAGEM", "ponte", "operacoes_unicas", len(por_num))
    ctl.add("CONTAGEM", "ponte", "linhas_duplicadas", sum(1 for l in linhas if l["flag_duplicata"]),
            ", ".join(n for n, q in por_num.items() if q > 1))
    ctl.add("CONTAGEM", "ponte", "spreads_negativos", sum(1 for l in linhas if l["flag_spread_negativo"]))
    ctl.add("CONTAGEM", "ponte", "operacoes_com_ressalva", sum(1 for l in linhas if l["flag_ressalva"]),
            "o status de compliance não muda nada para a Tarvo (financeiro)")
    ctl.add("CONTAGEM", "ponte", "liquidadas_no_mes_seguinte", sum(1 for l in linhas if l["flag_liquidacao_mes_seguinte"]),
            "vale a data de contratação (financeiro)")
    ctl.add("CONTAGEM", "ponte", "spreads_fora_da_tolerancia",
            sum(1 for l in linhas if l["flag_spread_diverge"] and not l["flag_duplicata"]),
            f"tolerância {params['tolerancia_spread_pp']} p.p. contra o spread contratado (padrão {params['spread_padrao_pct']}%)")
    ctl.add("CONTAGEM", "ponte", "cnpj_fora_da_tabela", sum(1 for l in linhas if l["flag_cnpj_fora_da_tabela"]))
    total = next((l for l in ctl.linhas if l["fonte"] == "ponte" and l["item"] == "total_declarado_operacoes"), None)
    if total is not None:
        ctl.verifica("ponte", "linhas_lidas_igual_total_declarado", len(linhas) == int(total["valor"]),
                     f"lidas={len(linhas)}; declarado={int(total['valor'])}")
    spread_decl = next((l for l in ctl.linhas if l["fonte"] == "ponte" and l["item"] == "total_declarado_spread_brl"), None)
    if spread_decl is not None:
        soma = round(sum(l["spread_brl"] for l in linhas), 2)
        ctl.verifica("ponte", "soma_spread_igual_total_declarado", abs(soma - float(spread_decl["valor"])) < 0.005,
                     f"soma={soma}; declarado={spread_decl['valor']}")
    return linhas


PROVISIONADOS = {"PAGTO SALARIOS", "GPS INSS", "GRF FGTS", "DEBITO DARF", "PAGTO ISS"}


def enriquecer_banco(registros: list[dict], ctl: Controle) -> None:
    """Acrescenta duas colunas que ajudam a classificar com contrapartida:
    competencia_declarada (mm/aaaa que o banco escreveu na descrição) e provisionado_antes (regra do financeiro)."""
    for r in registros:
        m = re.search(r"\b(\d{2})/(20\d{2})\b", r["descricao"])
        r["competencia_declarada"] = f"{m.group(2)}-{m.group(1)}" if m else ""
        comissao_ponte = r["tipo_lancamento"] == "TED RECEB" and "PONTE" in r["contraparte"].upper()
        r["provisionado_antes"] = r["tipo_lancamento"] in PROVISIONADOS or comissao_ponte
    ctl.add("REGRA", "fato_banco", "provisionado_antes",
            sum(1 for r in registros if r["provisionado_antes"]),
            "folha, GPS, GRF, DARF e ISS do mês anterior e o repasse de comissão da Ponte já estavam registrados; "
            "o pagamento baixa a provisão (Helena, financeiro, canal #tarvo-financeiro)")


# ----------------------------------------------------------------------------- principal
def montar_contratos(contratos: list[dict]) -> list[dict]:
    saida = []
    for c in contratos:
        saida.append({**c, "lojista_id": c["cnpj"]})
    return saida


def executar(mes: str, entrada: Path, saida: Path) -> dict[str, int]:
    ctl = Controle()
    f_orbe = achar_arquivo(entrada, "01_orbe", ".csv", mes)
    f_taxas = achar_arquivo(entrada, "02_tabela_taxas", ".xlsx", mes)
    f_ponte = achar_arquivo(entrada, "03_email_ponte", ".eml", mes)
    f_plano = achar_arquivo(entrada, "04_plano_de_contas", ".csv", mes)
    f_aurora = achar_arquivo(entrada, "05a_extrato_banco_aurora", ".csv", mes)
    f_meridiano = achar_arquivo(entrada, "05b_extrato_banco_meridiano", ".ofx", mes)

    complementos_orbe = achar_complementos_orbe(entrada, mes, f_orbe)
    orbe_raw = ler_orbe_completo(f_orbe, complementos_orbe, ctl)
    contratos = ler_tabela_taxas(f_taxas, ctl)
    ponte_raw, arquivo_ponte = ler_ponte(f_ponte, ctl)
    plano = ler_plano(f_plano, ctl)
    aurora = ler_aurora(f_aurora, mes, ctl)
    meridiano = ler_meridiano(f_meridiano, mes, ctl)
    # Decisões confirmadas pelo financeiro (config/): mapeamento de EC, condições comerciais e parâmetros.
    overrides = ler_overrides()
    params = ler_parametros()
    ctl.add("REGRA", "parametros", "spread_padrao_pct", params["spread_padrao_pct"],
            "célula em branco ou 'padrão' na tabela = 1,5% sobre a PTAX (Helena, financeiro)")
    ctl.add("REGRA", "parametros", "tolerancia_spread_pp", params["tolerancia_spread_pp"],
            "critério da equipe, escrito com motivo; o financeiro pediu não receber alarme de centavo")
    n_vinculos = vincular_ecs(contratos, overrides)
    ctl.add("CONTAGEM", "dim_ec", "linhas_da_tabela_com_ec_confirmado_pelo_financeiro", n_vinculos)
    contratos = aplicar_condicoes(contratos, ler_config("condicoes_comerciais.csv"), ctl)
    for c in contratos:
        c["spread_remessa_efetivo_pct"] = (c["spread_remessa_pct"] if c["spread_remessa_pct"] is not None
                                          else params["spread_padrao_pct"])

    dim_ec = construir_dim_ec(orbe_raw, contratos, overrides)
    checar_integridade_dim_ec(dim_ec, orbe_raw, contratos, overrides, ctl)
    dim_lojista = construir_dim_lojista(contratos, dim_ec, ponte_raw)
    contratos_out = montar_contratos(contratos)
    fato_orbe = construir_fato_orbe(orbe_raw, dim_ec, mes, ctl)
    fato_ponte = construir_fato_ponte(ponte_raw, arquivo_ponte, mes, contratos, params, ctl)
    fato_banco = aurora + meridiano
    enriquecer_banco(fato_banco, ctl)

    ctl.verifica("tabela_taxas", "cnpj_com_14_digitos", not any(c["cnpj_ajustado"] for c in contratos),
                 f"ajustados={sum(1 for c in contratos if c['cnpj_ajustado'])} (zero à esquerda restaurado)")
    ctl.add("CONTAGEM", "dim_ec", "ecs_nao_confirmados", sum(1 for e in dim_ec if e["status"] != "CONFIRMADO"),
            ", ".join(f"{e['ec']}={e['status']}" for e in dim_ec if e["status"] != "CONFIRMADO"))
    pendentes = [e["ec"] for e in dim_ec if e["status"] == "PENDENTE"]
    ctl.verifica("dim_ec", "nenhum_ec_da_orbe_sem_mapeamento", not pendentes,
                 f"pendentes={pendentes}" if pendentes else "todos os ECs da Orbe estão CONFIRMADO ou RETIDO")
    ecs_confirmados_financeiro = sorted(e["ec"] for e in dim_ec if e["fonte_mapeamento"] == "config/mapeamento_ec.csv"
                                        and e["status"] == "CONFIRMADO")
    ctl.add("CONTAGEM", "dim_ec", "ecs_confirmados_pelo_financeiro", len(ecs_confirmados_financeiro),
            ", ".join(ecs_confirmados_financeiro))
    ctl.verifica("fato_orbe", "linhas_com_cnpj_ou_retidas",
                 all(l["cnpj"] or l["status_ec"] == "RETIDO" for l in fato_orbe),
                 "toda linha da Orbe tem CNPJ, exceto as da EC retida (Atlas)")
    ctl.verifica("fato_banco", "ref_origem_unico", len({(b["banco"], b["ref_origem"]) for b in fato_banco}) == len(fato_banco))

    saida = Path(saida)
    contagem = {
        "dim_lojista": escrever_csv(saida / "dim_lojista.csv", dim_lojista, COL_DIM_LOJISTA),
        "dim_ec": escrever_csv(saida / "dim_ec.csv", dim_ec, COL_DIM_EC),
        "dim_contrato_taxa": escrever_csv(saida / "dim_contrato_taxa.csv", contratos_out, COL_DIM_CONTRATO),
        "dim_plano_contas": escrever_csv(saida / "dim_plano_contas.csv", plano, COL_DIM_PLANO),
        "fato_orbe": escrever_csv(saida / "fato_orbe.csv", fato_orbe, COL_FATO_ORBE),
        "fato_ponte": escrever_csv(saida / "fato_ponte.csv", fato_ponte, COL_FATO_PONTE),
        "fato_banco": escrever_csv(saida / "fato_banco.csv", fato_banco, COL_FATO_BANCO),
    }
    # Conservação: o que foi lido é o que foi gravado.
    for fonte, lidas, gravadas in [("orbe", len(orbe_raw), contagem["fato_orbe"]), ("ponte", len(ponte_raw), contagem["fato_ponte"]),
                                   ("plano_contas", len(plano), contagem["dim_plano_contas"]),
                                   ("bancos", len(aurora) + len(meridiano), contagem["fato_banco"])]:
        ctl.verifica(fonte, "linhas_lidas_igual_gravadas", lidas == gravadas, f"lidas={lidas}; gravadas={gravadas}")
    contagem["controle_ingestao"] = escrever_csv(saida / "controle_ingestao.csv", ctl.linhas, COL_CONTROLE)
    alertas = [l for l in ctl.linhas if l["tipo"] == "VERIFICACAO" and l["valor"] == "ALERTA"]
    for a in alertas:
        print(f"ALERTA [{a['fonte']}] {a['item']}: {a['detalhe']}", file=sys.stderr)
    return contagem


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ingestão do data pack da Tarvo em tabelas padronizadas (CSV).")
    ap.add_argument("--mes", required=True, help="competência AAAA-MM (usada também para achar os arquivos do mês)")
    ap.add_argument("--entrada", default="input", help="pasta com os arquivos brutos (todos os de entrada ficam aqui)")
    ap.add_argument("--saida", default="data", help="pasta onde as tabelas serão gravadas")
    a = ap.parse_args(argv)
    contagem = executar(a.mes, Path(a.entrada), Path(a.saida))
    print(f"Tabelas gravadas em {Path(a.saida).resolve()}")
    for nome, n in contagem.items():
        print(f"  {nome:<20}{n:>6} linhas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
