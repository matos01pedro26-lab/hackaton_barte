"""Utilitários de leitura e normalização compartilhados pelos módulos de ingestão.

Nada aqui decide regra de negócio: só abre arquivos e converte formatos.
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, timedelta
from pathlib import Path

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


# ---------------------------------------------------------------- arquivos
def ler_texto(caminho: Path) -> tuple[str, str]:
    """Lê os bytes e tenta UTF-8; se falhar, cai para cp1252. Devolve (texto, encoding)."""
    bruto = Path(caminho).read_bytes()
    for enc in ("utf-8", "cp1252"):
        try:
            return bruto.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return bruto.decode("latin-1"), "latin-1"


def sha256(caminho: Path) -> str:
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def achar_arquivo(entrada: Path, prefixo: str, extensao: str, mes: str) -> Path:
    """Acha o arquivo da fonte pelo prefixo e extensão. Se houver mais de um, prefere o do mês (ex.: 'set2026')."""
    ano, m = mes.split("-")
    marca = f"{MESES[int(m) - 1]}{ano}"
    candidatos = sorted(p for p in Path(entrada).glob(f"{prefixo}*{extensao}"))
    if not candidatos:
        raise FileNotFoundError(f"Nenhum arquivo '{prefixo}*{extensao}' em {Path(entrada).resolve()}")
    do_mes = [p for p in candidatos if marca in p.name.lower()]
    if len(do_mes) == 1:
        return do_mes[0]
    if len(candidatos) == 1:
        return candidatos[0]
    raise FileNotFoundError(f"Mais de um arquivo '{prefixo}*{extensao}' e nenhum identificado como {marca}: "
                            f"{[p.name for p in candidatos]}")


# ---------------------------------------------------------------- texto e identificadores
def sem_acento(s: str) -> str:
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()


def norm_nome(s: str) -> str:
    """MAIÚSCULAS, sem acento, sem pontuação. Só para comparar nomes; nunca para decidir ligação."""
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", sem_acento(s).upper())).strip()


def norm_cabecalho(s) -> str:
    """'Créd. 2-6x' -> 'cred26x'. Permite achar colunas por nome mesmo que mudem acento ou pontuação."""
    return re.sub(r"[^a-z0-9]", "", sem_acento(s or "").lower())


def so_digitos(s) -> str:
    return re.sub(r"\D", "", str(s or ""))


def cnpj14(s) -> tuple[str, bool]:
    """CNPJ só com dígitos. Devolve (cnpj, ajustado). Se vier com menos de 14 dígitos (zero à esquerda
    perdido pela planilha), completa com zeros e marca ajustado=True."""
    d = so_digitos(s)
    if not d:
        return "", False
    if len(d) < 14:
        return d.zfill(14), True
    return d, False


def ec_texto(s) -> str:
    """Código de estabelecimento como texto de dígitos ('1075624862.0' -> '1075624862')."""
    t = str(s or "").strip()
    t = re.sub(r"\.0+$", "", t)
    return so_digitos(t)


# ---------------------------------------------------------------- números e datas
def num_br(s) -> float | None:
    """'1.234,56' -> 1234.56 ; '2,69' -> 2.69 ; '' -> None."""
    t = str(s if s is not None else "").strip().replace("R$", "").replace("%", "").strip()
    if t == "":
        return None
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def num_ponto(s) -> float | None:
    """'5402.22' -> 5402.22 ; '' -> None."""
    t = str(s if s is not None else "").strip()
    if t == "":
        return None
    try:
        return float(t)
    except ValueError:
        return None


def pct_planilha(x) -> float | None:
    """Percentual da tabela de taxas, em pontos percentuais (1.49 = 1,49%).
    Aceita '1,49%' (texto) e 0.0149 (fração). Número sem '%' menor que 1 é tratado como fração."""
    if x is None:
        return None
    t = str(x).strip()
    if t == "" or not re.search(r"\d", t):
        return None
    if "%" in t:
        v = num_br(t)
        return None if v is None else round(v, 6)
    v = num_br(t)
    if v is None:
        return None
    return round(v * 100, 6) if v < 1 else round(v, 6)


def data_br(s) -> str:
    """'01/09/2026' -> '2026-09-01' ; vazio -> ''."""
    t = str(s or "").strip()
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", t)
    if not m:
        return ""
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"


def data_serial_excel(n) -> str:
    """Número serial do Excel -> 'AAAA-MM-DD'."""
    try:
        return (date(1899, 12, 30) + timedelta(days=int(float(n)))).isoformat()
    except (TypeError, ValueError):
        return ""


# ---------------------------------------------------------------- xlsx sem dependências
def ler_xlsx(origem) -> tuple[dict[str, dict[tuple[int, str], str]], list[tuple[str, str]]]:
    """Lê .xlsx (caminho ou bytes) sem openpyxl.
    Devolve ({aba: {(linha, coluna): valor}}, [(celula, comentario)]). Valores são texto, como estão no arquivo."""
    z = zipfile.ZipFile(io.BytesIO(origem) if isinstance(origem, (bytes, bytearray)) else origem)
    M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    textos: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(M + "si"):
            textos.append("".join(t.text or "" for t in si.iter(M + "t")))
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    pasta = ET.fromstring(z.read("xl/workbook.xml"))
    abas: dict[str, dict[tuple[int, str], str]] = {}
    for aba in pasta.find(M + "sheets"):
        alvo = rels[aba.get(R + "id")]
        caminho = alvo.lstrip("/") if alvo.startswith("/") else "xl/" + alvo
        celulas: dict[tuple[int, str], str] = {}
        for c in ET.fromstring(z.read(caminho)).iter(M + "c"):
            tipo, v = c.get("t"), c.find(M + "v")
            if tipo == "inlineStr":
                valor = "".join(x.text or "" for x in c.iter(M + "t"))
            elif v is None:
                continue
            elif tipo == "s":
                valor = textos[int(v.text)]
            else:
                valor = v.text or ""
            m = re.match(r"([A-Z]+)(\d+)", c.get("r"))
            celulas[(int(m.group(2)), m.group(1))] = valor
        abas[aba.get("name")] = celulas
    comentarios = []
    for nome in z.namelist():
        if nome.startswith("xl/comments"):
            for cm in ET.fromstring(z.read(nome)).iter(M + "comment"):
                comentarios.append((cm.get("ref"), "".join(t.text or "" for t in cm.iter(M + "t"))))
    return abas, comentarios


# ---------------------------------------------------------------- saída
def fmt(v) -> str:
    """Formata para CSV: vazio para None, ponto decimal, sem zeros sobrando."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "S" if v else "N"
    if isinstance(v, float):
        t = f"{v:.6f}".rstrip("0").rstrip(".")
        return "0" if t in ("", "-0") else t
    return str(v)


def escrever_csv(caminho: Path, linhas: list[dict], colunas: list[str]) -> int:
    """Grava CSV com ';' como separador, UTF-8, na ordem de colunas dada. Devolve o nº de linhas."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(colunas)
        for linha in linhas:
            faltando = set(linha) - set(colunas)
            if faltando:
                raise ValueError(f"Colunas fora do contrato em {caminho.name}: {sorted(faltando)}")
            w.writerow([fmt(linha.get(c)) for c in colunas])
    return len(linhas)
