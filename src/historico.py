"""Histórico dos meses fechados: o que o mês seguinte precisa saber do anterior.

Cada mês fechado fica em fechamentos/AAAA-MM/ (versionado no git):
    manifesto.json            mês, quando fechou, commit, arquivos de entrada (sha256) e totais
    saida/                    os seis arquivos entregues
    data/                     as tabelas que o mês seguinte consulta (fato_orbe, fato_ponte, fato_banco, dim_ec, controle)
    pendencias_abertas.csv    pendências do mês + herdadas que ninguém resolveu (config/pendencias_resolvidas.csv)

Regras (HIPOTESES P20 e P21):
  * mês fechado não reabre. Refazer só com pedido explícito (--refazer), e o fechamento anterior fica guardado;
  * o rastro arquivado é a prova do que já foi faturado: transação da Orbe faturada não entra de novo, e operação da
    Ponte faturada que reaparece no relatório seguinte conta uma vez.
Este módulo é o único que lê ou grava fechamentos/.
"""
from __future__ import annotations

import csv
import io
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from .utils import escrever_csv, ler_texto

RAIZ = Path(__file__).resolve().parents[1]
RAIZ_HIST = RAIZ / "fechamentos"
SAIDAS = ["comissoes_por_lojista", "divergencias_taxa", "notas_a_emitir", "lancamentos_classificados", "pendencias", "rastro"]
TABELAS = ["fato_orbe", "fato_ponte", "fato_banco", "dim_ec", "controle_ingestao"]
COL_PENDENCIAS = ["mes_origem", "id_saida", "tipo", "ref_origem", "valor_brl", "motivo", "quem_decide"]
MES = re.compile(r"^20\d\d-(0[1-9]|1[0-2])$")


class MesFechado(ValueError):
    """O mês já tem fechamento arquivado e não reabre sem pedido explícito."""


class CobrancaDuplicada(ValueError):
    """Uma transação da Orbe deste mês já foi faturada num mês fechado."""


def _csv(caminho: Path) -> list[dict]:
    if not Path(caminho).exists():
        return []
    texto, _ = ler_texto(caminho)
    return list(csv.DictReader(io.StringIO(texto), delimiter=";"))


def pasta(mes: str, raiz: Path = RAIZ_HIST) -> Path:
    return Path(raiz) / mes


def esta_fechado(mes: str, raiz: Path = RAIZ_HIST) -> bool:
    return (pasta(mes, raiz) / "manifesto.json").exists()


def meses_fechados(raiz: Path = RAIZ_HIST) -> list[str]:
    raiz = Path(raiz)
    if not raiz.is_dir():
        return []
    return sorted(p.name for p in raiz.iterdir() if MES.match(p.name) and (p / "manifesto.json").exists())


def mes_anterior(mes: str) -> str:
    ano, m = map(int, mes.split("-"))
    return f"{ano - 1}-12" if m == 1 else f"{ano}-{m - 1:02d}"


def chaves_faturadas(raiz: Path = RAIZ_HIST, antes_de: str | None = None) -> dict[str, dict[str, str]]:
    """{'orbe': {id_transacao: mês}, 'ponte': {num_op: mês}} do que entrou em comissão nos meses fechados antes de antes_de.
    A fonte é o rastro arquivado: CHK-… aponta para transações da Orbe, REM-… para operações da Ponte."""
    faturadas: dict[str, dict[str, str]] = {"orbe": {}, "ponte": {}}
    for mes in meses_fechados(raiz):
        if antes_de is not None and mes >= antes_de:
            continue
        for r in _csv(pasta(mes, raiz) / "saida" / "rastro.csv"):
            if r["id_saida"].startswith("CHK-"):
                faturadas["orbe"].setdefault(r["ref_origem"], mes)
            elif r["id_saida"].startswith("REM-"):
                faturadas["ponte"].setdefault(r["ref_origem"], mes)
    return faturadas


def conferir(dados: Path, mes: str, raiz: Path = RAIZ_HIST) -> dict[str, str]:
    """Compara o mês com o histórico. Para se uma transação da Orbe já foi faturada (cobrança em dobro).
    Devolve {num_op: mês} das operações da Ponte já faturadas, que a remessa conta uma vez só."""
    faturadas = chaves_faturadas(raiz, antes_de=mes)
    repetidas = sorted({l["id_transacao"] for l in _csv(Path(dados) / "fato_orbe.csv")} & set(faturadas["orbe"]))
    if repetidas:
        exemplos = ", ".join(f"{t} ({faturadas['orbe'][t]})" for t in repetidas[:10])
        raise CobrancaDuplicada(f"{len(repetidas)} transação(ões) da Orbe deste arquivo já foram faturadas em mês fechado: "
                                f"{exemplos}{' …' if len(repetidas) > 10 else ''}. Confira se o relatório é mesmo de {mes}.")
    ops = {l["num_op"] for l in _csv(Path(dados) / "fato_ponte.csv")}
    return {op: m for op, m in faturadas["ponte"].items() if op in ops}


def resolvidas(config: Path) -> set[str]:
    """id_saida das pendências que a Helena (ou quem decide) já resolveu: config/pendencias_resolvidas.csv."""
    return {r["id_saida"] for r in _csv(Path(config) / "pendencias_resolvidas.csv") if r.get("id_saida")}


def pendencias_herdadas(mes: str, config: Path, raiz: Path = RAIZ_HIST) -> list[dict]:
    """Pendências ainda abertas do último mês fechado antes de mes (cada uma com o mês em que nasceu)."""
    anteriores = [m for m in meses_fechados(raiz) if m < mes]
    if not anteriores:
        return []
    feitas = resolvidas(config)
    return [p for p in _csv(pasta(anteriores[-1], raiz) / "pendencias_abertas.csv") if p["id_saida"] not in feitas]


def _arquivos_de_entrada(controle: list[dict]) -> list[dict]:
    """Nome e sha256 de cada arquivo lido, a partir de controle_ingestao (cada 'arquivo' é seguido do seu 'sha256')."""
    saida, ultimo = [], {}
    for l in controle:
        if l["tipo"] != "ARQUIVO":
            continue
        if l["item"] == "arquivo":
            ultimo[l["fonte"]] = l["valor"]
        elif l["item"] == "sha256":
            saida.append({"fonte": l["fonte"], "arquivo": ultimo.get(l["fonte"], l["detalhe"]), "sha256": l["valor"]})
    return saida


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RAIZ, capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _guardar_anterior(destino: Path) -> str:
    """Move o fechamento existente para destino/anterior_<hora>/ e devolve o nome da pasta."""
    nome = f"anterior_{datetime.now():%Y%m%d_%H%M%S}"
    guarda = destino / nome
    guarda.mkdir()
    for p in list(destino.iterdir()):
        if p != guarda and not p.name.startswith("anterior_"):
            shutil.move(str(p), str(guarda / p.name))
    return nome


def arquivar(mes: str, dados: Path, saida: Path, config: Path, totais: dict, raiz: Path = RAIZ_HIST,
             refazer: bool = False) -> Path:
    """Grava fechamentos/AAAA-MM/. Só deve ser chamado depois que o validador passou."""
    destino = pasta(mes, raiz)
    anteriores: list[str] = []
    if esta_fechado(mes, raiz):
        if not refazer:
            raise MesFechado(f"{mes} já está fechado ({destino}). Mês fechado não reabre; use --refazer só para corrigir "
                             "um fechamento errado (o anterior fica guardado).")
        anteriores = json.loads((destino / "manifesto.json").read_text(encoding="utf-8")).get("anteriores", [])
        anteriores.append(_guardar_anterior(destino))
    (destino / "saida").mkdir(parents=True, exist_ok=True)
    (destino / "data").mkdir(parents=True, exist_ok=True)
    for n in SAIDAS:
        shutil.copy2(Path(saida) / f"{n}.csv", destino / "saida" / f"{n}.csv")
    for n in TABELAS:
        if (Path(dados) / f"{n}.csv").exists():
            shutil.copy2(Path(dados) / f"{n}.csv", destino / "data" / f"{n}.csv")

    abertas = [{"mes_origem": mes, **p} for p in _csv(Path(saida) / "pendencias.csv")]
    abertas += pendencias_herdadas(mes, config, raiz)
    escrever_csv(destino / "pendencias_abertas.csv", abertas, COL_PENDENCIAS)

    manifesto = {
        "mes": mes, "fechado_em": datetime.now().isoformat(timespec="seconds"), "commit": _commit(),
        "arquivos_de_entrada": _arquivos_de_entrada(_csv(Path(dados) / "controle_ingestao.csv")),
        "totais": totais, "pendencias_abertas": len(abertas), "anteriores": anteriores,
    }
    (destino / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino
