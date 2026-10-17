"""Ingestão: transforma os arquivos brutos do data pack em tabelas padronizadas (CSV) na pasta de saída.

Uso (a partir da raiz do repositório):
    python -m src.ingestao --mes 2026-09 --entrada . --saida data

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
from decimal import Decimal, ROUND_DOWN
from email import policy
from pathlib import Path

from .utils import (achar_arquivo, cnpj14, data_br, data_serial_excel, ec_texto, escrever_csv, ler_texto,
                    ler_xlsx, norm_cabecalho, norm_nome, num_br, num_ponto, pct_planilha, sha256, so_digitos)

# ----------------------------------------------------------------------------- esquemas das tabelas
COL_DIM_LOJISTA = ["lojista_id", "cnpj", "cnpj_ajustado", "nome_canonico", "nomes_alternativos", "ecs", "ativo",
                   "linha_checkout", "linha_remessa", "status_cadastro", "obs_tabela", "linha_planilha"]
COL_DIM_EC = ["ec", "status", "faturavel", "lojista_id", "cnpj", "nome_tabela", "nomes_orbe", "n_linhas_orbe",
              "fonte_mapeamento", "sugestao_cnpj", "sugestao_nome_tabela", "observacao"]
COL_DIM_CONTRATO = ["lojista_id", "cnpj", "cnpj_ajustado", "ec", "nome_tabela", "vigencia_ini", "vigencia_fim", "taxa_debito_pct",
                    "taxa_credito_vista_pct", "taxa_credito_2_6x_pct", "taxa_credito_7_12x_pct", "taxa_pix_pct",
                    "taxa_antecipacao_pct", "spread_remessa_pct", "spread_remessa_regra", "pct_em_texto", "obs",
                    "comentario_celula", "linha_planilha"]
COL_DIM_PLANO = ["cod_conta", "descricao", "tipo", "natureza", "aceita_lancamento", "cod_superior", "nivel",
                 "dt_criacao"]
COL_FATO_ORBE = ["competencia", "arquivo_origem", "linha_origem", "id_transacao", "data_movimento", "ec",
                 "status_ec", "cnpj", "nome_estabelecimento", "tipo_lancamento", "modalidade", "faixa", "parcelas",
                 "bandeira", "valor_bruto", "taxa_aplicada_pct", "valor_taxa", "valor_liquido", "id_referencia",
                 "data_venda_original", "data_taxa_ref", "flag_ref_sem_origem", "flag_venda_mes_anterior"]
COL_FATO_PONTE = ["competencia", "arquivo_origem", "linha_origem", "num_op", "data_contratacao", "data_liquidacao",
                  "cnpj", "cnpj_ajustado", "cliente_nome", "moeda", "valor_me", "taxa_cliente", "ptax", "valor_brl",
                  "spread_brl", "spread_pct", "spread_estimado_brl", "iof_brl", "status_compliance", "observacao",
                  "flag_duplicata", "flag_spread_negativo", "flag_ressalva"]
COL_FATO_BANCO = ["competencia", "banco", "ref_origem", "arquivo_origem", "linha_origem", "data", "descricao",
                  "documento", "valor", "sentido", "saldo", "tipo_lancamento", "contraparte", "contraparte_cnpj"]
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
def ler_orbe(caminho: Path, ctl: Controle) -> list[dict]:
    texto, enc = ler_texto(caminho)
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    faltando = [c for c in ORBE_COLUNAS if c not in (leitor.fieldnames or [])]
    if faltando:
        raise ValueError(f"Orbe fora do contrato: faltam colunas {faltando}")
    linhas = []
    for r in leitor:
        r = {k: (v or "").strip() for k, v in r.items()}
        r["_linha"] = leitor.line_num
        linhas.append(r)
    ctl.add("ARQUIVO", "orbe", "arquivo", caminho.name, f"encoding={enc}")
    ctl.add("ARQUIVO", "orbe", "sha256", sha256(caminho))
    ctl.add("CONTAGEM", "orbe", "linhas_lidas", len(linhas))
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
def ler_overrides(caminho: Path) -> dict[str, dict]:
    if not caminho.exists():
        return {}
    texto, _ = ler_texto(caminho)
    return {ec_texto(r["ec"]): {k: (v or "").strip() for k, v in r.items()}
            for r in csv.DictReader(io.StringIO(texto), delimiter=";") if (r.get("ec") or "").strip()}


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

    linhas = []
    for ec in sorted(n_linhas):
        ov = overrides.get(ec)
        sugestao_cnpj, sugestao_nome, obs = "", "", ""
        if ov and ov.get("status"):
            status, cnpj, fonte = ov["status"].upper(), cnpj14(ov.get("cnpj", ""))[0], "config/mapeamento_ec.csv"
            obs = ov.get("fonte", "")
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
        linhas.append({
            "ec": ec, "status": status, "faturavel": status == "CONFIRMADO", "lojista_id": "", "cnpj": cnpj,
            "nome_tabela": nome_tabela, "nomes_orbe": " | ".join(sorted(nomes[ec])), "n_linhas_orbe": n_linhas[ec],
            "fonte_mapeamento": fonte, "sugestao_cnpj": sugestao_cnpj, "sugestao_nome_tabela": sugestao_nome,
            "observacao": obs,
        })
    for l in linhas:
        l["lojista_id"] = l["cnpj"] if l["cnpj"] else f"EC{l['ec']}"
    return linhas


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
            "obs_tabela": " | ".join(x for x in {r["obs"] for r in rows} if x),
            "linha_planilha": " | ".join(str(r["linha_planilha"]) for r in rows),
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
def construir_fato_orbe(orbe: list[dict], dim_ec: list[dict], arquivo: str, competencia: str,
                        ctl: Controle) -> list[dict]:
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
            "competencia": competencia, "arquivo_origem": arquivo, "linha_origem": r["_linha"],
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


def construir_fato_ponte(ops: list[dict], arquivo: str, competencia: str, ctl: Controle) -> list[dict]:
    vistos: Counter = Counter()
    linhas = []
    for o in ops:
        vistos[o["num_op"]] += 1
        cnpj, ajustado = cnpj14(o["cnpj"])
        spread = num_ponto(o["spread_brl"])
        frac = num_ponto(o["spread_pct"])
        linhas.append({
            "competencia": competencia, "arquivo_origem": arquivo, "linha_origem": o["_linha"],
            "num_op": o["num_op"], "data_contratacao": data_serial_excel(o["data_contratacao"]),
            "data_liquidacao": data_serial_excel(o["data_liquidacao"]), "cnpj": cnpj, "cnpj_ajustado": ajustado,
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
    ctl.add("CONTAGEM", "ponte", "operacoes_com_ressalva", sum(1 for l in linhas if l["flag_ressalva"]))
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

    orbe_raw = ler_orbe(f_orbe, ctl)
    contratos = ler_tabela_taxas(f_taxas, ctl)
    ponte_raw, arquivo_ponte = ler_ponte(f_ponte, ctl)
    plano = ler_plano(f_plano, ctl)
    aurora = ler_aurora(f_aurora, mes, ctl)
    meridiano = ler_meridiano(f_meridiano, mes, ctl)
    overrides = ler_overrides(Path(__file__).resolve().parent.parent / "config" / "mapeamento_ec.csv")

    dim_ec = construir_dim_ec(orbe_raw, contratos, overrides)
    dim_lojista = construir_dim_lojista(contratos, dim_ec, ponte_raw)
    contratos_out = montar_contratos(contratos)
    fato_orbe = construir_fato_orbe(orbe_raw, dim_ec, f_orbe.name, mes, ctl)
    fato_ponte = construir_fato_ponte(ponte_raw, arquivo_ponte, mes, ctl)
    fato_banco = aurora + meridiano

    ctl.verifica("tabela_taxas", "cnpj_com_14_digitos", not any(c["cnpj_ajustado"] for c in contratos),
                 f"ajustados={sum(1 for c in contratos if c['cnpj_ajustado'])} (zero à esquerda restaurado)")
    ctl.add("CONTAGEM", "dim_ec", "ecs_nao_confirmados", sum(1 for e in dim_ec if e["status"] != "CONFIRMADO"),
            ", ".join(f"{e['ec']}={e['status']}" for e in dim_ec if e["status"] != "CONFIRMADO"))
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
    ap.add_argument("--mes", default="2026-09", help="competência AAAA-MM (usada também para achar os arquivos do mês)")
    ap.add_argument("--entrada", default=".", help="pasta com os arquivos brutos")
    ap.add_argument("--saida", default="data", help="pasta onde as tabelas serão gravadas")
    a = ap.parse_args(argv)
    contagem = executar(a.mes, Path(a.entrada), Path(a.saida))
    print(f"Tabelas gravadas em {Path(a.saida).resolve()}")
    for nome, n in contagem.items():
        print(f"  {nome:<20}{n:>6} linhas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
