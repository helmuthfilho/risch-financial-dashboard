#!/usr/bin/env python3
"""Demonstrações padronizadas (ITR/DFP) de companhias abertas via CVM Dados Abertos.

Uso:
  cvm_cia.py resumo PETR4 [--trimestres 8] [--individual]
      Tabela trimestral (colunas = trimestres + LTM) com receita, margens,
      EBITDA (EBIT + D&A da DVA), lucro, FCO, capex, FCL, dívida líquida,
      DL/EBITDA, ROE, liquidez, alíquota efetiva; + cadastro, auditor e
      tipo de parecer/revisão de cada período.
  cvm_cia.py contas PETR4 --codigos 3.01,3.04.02,2.01.04 [--trimestres 8]
      Contas específicas pelo código do plano padronizado da CVM.
  cvm_cia.py contas TAEE11 --nome "dividend|juros sobre o capital" [--excluir "n[ãa]o controlador"]
                    [--prefixo 6.03 | --demonstracao DFC] [--nivel 3] [--trimestres 8]
      Contas escolhidas pelo *nome* em cada período (use para contas não fixas,
      cujo código muda entre ITR e DFP); mostra os códigos usados em cada período.
  cvm_cia.py plano PETR4 --demonstracao DRE [--nivel 3]
      Lista códigos/nomes de contas do último período (para achar códigos).
  cvm_cia.py pares PETR4 [--top 10] [--setor "Petróleo e Gás"]
      Companhias ativas com ação em bolsa no mesmo setor da CVM (holdings do
      setor incluídas), ordenadas pela receita da última DFP. É uma lista de
      candidatos: o setor da CVM é amplo, então escolha os comparáveis.
  cvm_cia.py resolver PETR4

Aceita ticker (via FCA) ou CNPJ. Trimestres de fluxo (DRE, DFC, DVA) são
isolados: o 4º tri vem de DFP anual menos o acumulado de 9 meses; DFC/DVA
(que a CVM só publica acumulados) são diferenciados trimestre a trimestre.

Os ZIPs (≈20 MB/ano cada, ITR e DFP) ficam em .cache/analise-fii-acoes/cvm/;
as linhas já filtradas da empresa ficam em JSON ao lado — chamadas seguintes
não varrem os ZIPs de novo. Valores em R$ milhões.

Limite: bancos e seguradoras usam outro plano de contas; para eles o resumo
mostra só as contas principais (use `plano` + `contas`) e os indicadores
setoriais (NPL, Basileia, índice combinado) precisam vir do release.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import unicodedata
from collections import defaultdict
from datetime import date
from typing import Dict, List, Optional, Tuple

from _comum import (
    cache_path,
    cvm_max_age,
    die,
    div,
    download_cached,
    fmt_mi,
    fmt_num,
    fmt_pct,
    iter_zip_csv,
    json_cache_get,
    json_cache_put,
    only_digits,
    print_table,
    quarter_label,
    to_cents,
    warn,
)

BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA"
STMTS = ("BPA", "BPP", "DRE", "DFC_MI", "DFC_MD", "DVA")
FLOW = ("DRE", "DFC", "DVA")
CACHE_VERSION = 4  # incrementar ao mudar o formato/critério do JSON de linhas filtradas

# Parágrafos reais do relatório do auditor. O texto padrão de responsabilidades
# ("...concluímos... se existe incerteza relevante... continuidade operacional")
# aparece em todo relatório e não pode disparar o alerta.
INCERTEZA_RX = re.compile(r"incerteza (significativa|relevante) relacionada (com|[àa]) (a )?continuidade", re.I)
# No texto da CVM as quebras de linha somem ("...Mobiliários.Ênfase - Informações
# comparativasChamamos a atenção para a Nota 2(a)..."): o título vem colado.
# "Chamamos a atenção para" é a frase-padrão do parágrafo de ênfase; o texto de
# responsabilidades usa "devemos chamar atenção", que não casa.
ENFASE_RX = re.compile(
    r"[êe]nfases?\s*[-–:]|par[áa]grafo de [êe]nfase|[êe]nfases?\s+em\b|chamamos\s+(a\s+)?aten[çc][ãa]o\s+para", re.I
)
ENFASE_TEMA_RX = re.compile(r"[êe]nfases?\s*[-–:]\s*(.{3,90}?)(?=chamamos|conforme|$)", re.I)
# sem título ("Chamamos a atenção para a Nota Explicativa nº 2 às..."): usa a nota citada
ENFASE_NOTA_RX = re.compile(r"chamamos\s+(?:a\s+)?aten[çc][ãa]o\s+para\s+(?:a\s+|o\s+)?(nota[^,.;]{0,40}?)(?=\s+(?:às|as|das|que|da|do)\b|[,.;]|$)", re.I)


def tema_enfase(txt: str) -> str:
    m = ENFASE_TEMA_RX.search(txt)
    if m:
        return m.group(1).strip(" .-")
    m = ENFASE_NOTA_RX.search(txt)
    return f"ver {m.group(1).strip()}" if m else ""

# ------------------------------------------------------------ resolução


def resolve(ident: str) -> Dict[str, str]:
    digits = only_digits(ident)
    this_year = time.localtime().tm_year
    cnpj = None
    tickers: List[str] = []
    for y in (this_year, this_year - 1):
        z = download_cached(
            f"{BASE}/DOC/FCA/DADOS/fca_cia_aberta_{y}.zip", cache_path("cvm", "cia", f"fca_cia_aberta_{y}.zip"), cvm_max_age(y)
        )
        if z is None:
            continue
        rows = list(iter_zip_csv(z, f"fca_cia_aberta_valor_mobiliario_{y}.csv"))
        if len(digits) == 14:
            cnpj = f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
        else:
            hit = [r for r in rows if r.get("Codigo_Negociacao", "").upper() == ident.upper()]
            if hit:
                cnpj = hit[0]["CNPJ_Companhia"]
        if cnpj:
            tickers = sorted({r["Codigo_Negociacao"] for r in rows if r["CNPJ_Companhia"] == cnpj and r.get("Codigo_Negociacao")})
            break
    if not cnpj:
        die(f"'{ident}' não encontrado no FCA da CVM (é FII? tente cvm_fii.py; BDR/ETF não têm ITR)")
    cad_path = download_cached(f"{BASE}/CAD/DADOS/cad_cia_aberta.csv", cache_path("cvm", "cia", "cad_cia_aberta.csv"), 7 * 24 * 3600)
    info: Dict[str, str] = {"CNPJ_CIA": cnpj}
    if cad_path is not None:
        import csv

        with open(cad_path, encoding="latin-1", newline="") as fh:
            for r in csv.DictReader(fh, delimiter=";"):
                if r["CNPJ_CIA"] == cnpj and (not info.get("SIT") or r.get("SIT") == "ATIVO"):
                    info.update(r)
    info["TICKERS"] = ",".join(tickers)
    return info


# ------------------------------------------------------------------ pares

# "Lucro/Prejuízo Consolidado do Período" (padrão) ou "Lucro ou Prejuízo Líquido
# Consolidado do Período" (ex.: Banco do Brasil)
LL_RX = r"^lucro\s*(/|ou)\s*preju[íi]zo\s+(l[íi]quido\s+)?(consolidado\s+)?do\s+per[íi]odo"

STOP = {"e", "de", "do", "da", "dos", "das"}
TICKER_RX = re.compile(r"[A-Z]{4}\d{1,2}")


def core_setor(setor: str) -> str:
    """Tira o prefixo de holding: "Emp. Adm. Part. - Energia Elétrica" -> "Energia Elétrica"."""
    return re.sub(r"^\s*emp\.?\s*adm\.?\s*part\.?\s*-\s*", "", setor or "", flags=re.I).strip()


def radicais(setor: str) -> set:
    s = unicodedata.normalize("NFKD", core_setor(setor).lower())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return {w[:3] for w in re.findall(r"[a-z]+", s) if w not in STOP}


def mesmo_setor(a: str, b: str) -> bool:
    """Compara setores pelo radical das palavras (a CVM abrevia diferente nas holdings:
    "Const. Civil, Mat. Const." x "Construção Civil, Mat. Constr.")."""
    ra, rb = radicais(a), radicais(b)
    return bool(ra and rb) and len(ra & rb) / len(ra | rb) >= 0.6


def tickers_em_bolsa() -> Dict[str, List[str]]:
    """CNPJ -> tickers negociados (FCA mais recente disponível)."""
    this_year = time.localtime().tm_year
    for y in (this_year, this_year - 1):
        z = download_cached(
            f"{BASE}/DOC/FCA/DADOS/fca_cia_aberta_{y}.zip", cache_path("cvm", "cia", f"fca_cia_aberta_{y}.zip"), cvm_max_age(y)
        )
        if z is None:
            continue
        out: Dict[str, set] = defaultdict(set)
        segmento: Dict[str, str] = {}
        for r in iter_zip_csv(z, f"fca_cia_aberta_valor_mobiliario_{y}.csv"):
            t = (r.get("Codigo_Negociacao") or "").strip().upper()
            # só códigos no formato B3 (4 letras + 1-2 dígitos); o FCA tem placeholders como "000000"
            if TICKER_RX.fullmatch(t) and not (r.get("Data_Fim_Negociacao") or "").strip():
                out[r["CNPJ_Companhia"]].add(t)
                if r.get("Segmento"):
                    segmento[r["CNPJ_Companhia"]] = r["Segmento"]
        tickers_em_bolsa.segmento = segmento  # type: ignore[attr-defined]
        return {k: sorted(v) for k, v in out.items()}
    die("FCA da CVM indisponível")
    return {}


def cadastro_ativos() -> Dict[str, Dict[str, str]]:
    import csv

    cad_path = download_cached(f"{BASE}/CAD/DADOS/cad_cia_aberta.csv", cache_path("cvm", "cia", "cad_cia_aberta.csv"), 7 * 24 * 3600)
    if cad_path is None:
        die("cadastro de companhias da CVM indisponível")
    out: Dict[str, Dict[str, str]] = {}
    with open(cad_path, encoding="latin-1", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            if r.get("SIT") == "ATIVO":
                out[r["CNPJ_CIA"]] = r
    return out


def receita_anual(cnpjs: set) -> Tuple[Optional[int], Dict[str, int]]:
    """Receita (3.01) da DFP mais recente para cada CNPJ; consolidada, senão individual."""
    this_year = time.localtime().tm_year
    for y in (this_year - 1, this_year - 2):
        name = f"dfp_cia_aberta_{y}.zip"
        z = download_cached(f"{BASE}/DOC/DFP/DADOS/{name}", cache_path("cvm", "cia", name), cvm_max_age(y))
        if z is None:
            continue
        out: Dict[str, Tuple[int, int]] = {}
        for consol in ("con", "ind"):
            falta = {c for c in cnpjs if c not in out}
            if not falta:
                break
            for r in iter_zip_csv(z, f"dfp_cia_aberta_DRE_{consol}_{y}.csv", lambda line: line[:18] in falta):
                if r.get("CD_CONTA") != "3.01" or r.get("ORDEM_EXERC") != "ÚLTIMO" or r["CNPJ_CIA"] not in falta:
                    continue
                ver = int(r["VERSAO"] or 0)
                cents = to_cents(r["VL_CONTA"])
                if cents is None:
                    continue
                scale = 1000 if r.get("ESCALA_MOEDA", "").upper() == "MIL" else 1
                if r["CNPJ_CIA"] not in out or ver >= out[r["CNPJ_CIA"]][0]:
                    out[r["CNPJ_CIA"]] = (ver, cents * scale)
        if out:
            return y, {k: v for k, (_, v) in out.items()}
    return None, {}


def cmd_pares(ident: str, top: int, setor: Optional[str]) -> None:
    info = resolve(ident)
    cnpj = info["CNPJ_CIA"]
    header(info)
    cad = cadastro_ativos()
    tick = tickers_em_bolsa()
    segmento = getattr(tickers_em_bolsa, "segmento", {})
    setores = sorted({core_setor(r.get("SETOR_ATIV", "")) for r in cad.values()} - {""})

    alvo = setor or info.get("SETOR_ATIV", "")
    if setor and not any(mesmo_setor(setor, x) for x in setores):
        die(f"setor '{setor}' não encontrado. Setores da CVM: {'; '.join(setores)}")
    if re.search(r"sem setor", alvo, re.I):
        die(f"setor da companhia é '{alvo}' (genérico); informe --setor. Setores: {'; '.join(setores)}")

    pares = {c for c, r in cad.items() if c in tick and mesmo_setor(r.get("SETOR_ATIV", ""), alvo)}
    pares.add(cnpj)
    ano, receita = receita_anual(pares)
    ranked = sorted((c for c in pares if c != cnpj), key=lambda c: receita.get(c, -1), reverse=True)[:top]
    origem = "informado via --setor" if setor else "da companhia"
    print(
        f"\nCandidatos a par — setor '{core_setor(alvo)}' ({origem}, holdings incluídas), com ação em bolsa; "
        f"{len(pares) - 1} encontrados, top {min(top, len(pares) - 1)} por receita {ano or '-'}:"
    )
    linhas = []
    for c in [cnpj] + ranked:
        r = cad.get(c, info)
        linhas.append(
            [
                ("▶ " if c == cnpj else "") + ",".join(tick.get(c, info.get("TICKERS", "").split(",")))[:24],
                (r.get("DENOM_COMERC") or r.get("DENOM_SOCIAL") or "")[:36],
                fmt_mi(receita.get(c)),
                (r.get("SETOR_ATIV") or "")[:34],
                (segmento.get(c) or "-")[:22],
                (r.get("CONTROLE_ACIONARIO") or "-")[:14],
            ]
        )
    print_table(["Tickers", "Empresa", f"Receita {ano or ''} R$ mi", "Setor CVM", "Listagem", "Controle"], linhas)
    print(
        "Lista de candidatos: o setor da CVM é amplo (ex.: junta integrada, junior e distribuidora). "
        "Proponha 2–4 comparáveis ao usuário e confirme antes de rodar `resumo` para cada um."
    )


def header(info: Dict[str, str]) -> None:
    print(
        f"{info.get('DENOM_SOCIAL', '?')} | CNPJ {info['CNPJ_CIA']} | CVM {info.get('CD_CVM', '?')} | "
        f"tickers: {info.get('TICKERS') or '-'} | setor: {info.get('SETOR_ATIV') or '-'} | "
        f"controle: {info.get('CONTROLE_ACIONARIO') or '-'} | auditor atual: {info.get('AUDITOR') or '-'}"
    )


# -------------------------------------------------------------- extração


def load_doc_year(doc: str, year: int, cnpj: str, consol: str) -> Tuple[List[dict], List[dict]]:
    """Linhas (já filtradas e na última versão) de um ITR/DFP de um ano + pareceres."""
    name = f"{doc}_cia_aberta_{year}.zip"
    zpath = download_cached(f"{BASE}/DOC/{doc.upper()}/DADOS/{name}", cache_path("cvm", "cia", name), cvm_max_age(year))
    if zpath is None:
        return [], []
    cp = cache_path("cvm", "cia", "empresas", only_digits(cnpj), f"v{CACHE_VERSION}_{doc}_{year}_{consol}.json")
    if cp.exists() and cp.stat().st_mtime >= zpath.stat().st_mtime:
        cached = json_cache_get(cp, float("inf"))
        return cached["linhas"], cached["pareceres"]

    pre = lambda line: line.startswith(cnpj)  # noqa: E731
    linhas: List[dict] = []
    for stmt in STMTS:
        for r in iter_zip_csv(zpath, f"{doc}_cia_aberta_{stmt}_{consol}_{year}.csv", pre):
            if r.get("ORDEM_EXERC") != "ÚLTIMO":
                continue
            scale = 1000 if r.get("ESCALA_MOEDA", "").upper() == "MIL" else 1
            cents = to_cents(r["VL_CONTA"])
            linhas.append(
                {
                    "st": "DFC" if stmt.startswith("DFC") else stmt,
                    "ref": r["DT_REFER"],
                    "ver": int(r["VERSAO"] or 0),
                    "ini": r.get("DT_INI_EXERC", ""),
                    "fim": r["DT_FIM_EXERC"],
                    "cd": r["CD_CONTA"],
                    "ds": r["DS_CONTA"],
                    "v": None if cents is None else cents * scale,
                }
            )
    best: Dict[str, int] = {}
    for x in linhas:
        best[x["ref"]] = max(best.get(x["ref"], 0), x["ver"])
    linhas = [x for x in linhas if x["ver"] == best[x["ref"]]]

    pareceres = []
    for r in iter_zip_csv(zpath, f"{doc}_cia_aberta_parecer_{year}.csv", pre):
        # ITR usa TP_RELAT_ESP (revisão especial); DFP usa TP_RELAT_AUD (auditoria)
        tipo = r.get("TP_RELAT_ESP") or r.get("TP_RELAT_AUD")
        if not tipo or int(r["VERSAO"] or 0) != best.get(r["DT_REFER"], -1):
            continue
        txt = r.get("TXT_PARECER_DECL", "").lower()
        pareceres.append(
            {
                "ref": r["DT_REFER"],
                "tipo": tipo,
                "doc": r.get("TP_PARECER_DECL", ""),
                "enfase": bool(ENFASE_RX.search(txt)),
                "enfase_tema": tema_enfase(r.get("TXT_PARECER_DECL", "")),
                "incerteza": bool(INCERTEZA_RX.search(txt)),
            }
        )
    json_cache_put(cp, {"linhas": linhas, "pareceres": pareceres})
    return linhas, pareceres


def month_diff(a: str, b: str) -> int:
    return (int(b[:4]) - int(a[:4])) * 12 + int(b[5:7]) - int(a[5:7])


def months_between(a: str, b: str) -> int:
    da, db = date.fromisoformat(a), date.fromisoformat(b)
    return (db.year - da.year) * 12 + db.month - da.month + (1 if db.day >= da.day - 1 else 0)


class Dados:
    """Séries por período: balanço (ponto no tempo) e fluxos trimestrais isolados."""

    def __init__(self, linhas: List[dict]):
        self.labels: Dict[str, Dict[str, str]] = defaultdict(dict)  # st -> cd -> ds
        self.bal: Dict[str, Dict[str, int]] = defaultdict(dict)  # fim -> cd -> v
        self._ds_bal: Dict[Tuple[str, str], Dict[str, str]] = defaultdict(dict)  # (BPA|BPP, fim) -> cd -> ds
        ytd: Dict[str, Dict[str, Dict[str, int]]] = {s: defaultdict(dict) for s in FLOW}
        q3m: Dict[str, Dict[str, Dict[str, int]]] = {s: defaultdict(dict) for s in FLOW}
        fy_start: Dict[str, Dict[str, str]] = {s: {} for s in FLOW}

        by_st_fim: Dict[Tuple[str, str], List[dict]] = defaultdict(list)
        for x in linhas:
            self.labels[x["st"]].setdefault(x["cd"], x["ds"])
            if x["v"] is None:
                continue
            if x["st"] in ("BPA", "BPP"):
                self.bal[x["fim"]][x["cd"]] = x["v"]
                self._ds_bal[(x["st"], x["fim"])][x["cd"]] = x["ds"]
            else:
                by_st_fim[(x["st"], x["fim"])].append(x)

        # nome de cada conta *no período*: contas não fixas mudam de código entre
        # períodos (ex.: dividendos pagos 6.03.09 no ITR e 6.03.07 na DFP)
        self.ds_periodo: Dict[Tuple[str, str], Dict[str, str]] = defaultdict(dict)
        for (st, fim), xs in by_st_fim.items():
            start = min(x["ini"] for x in xs)
            fy_start[st][fim] = start
            for x in xs:
                if x["ini"] == start:
                    ytd[st][fim][x["cd"]] = x["v"]
                    self.ds_periodo[(st, fim)][x["cd"]] = x["ds"]
                elif months_between(x["ini"], fim) == 3:
                    q3m[st][fim][x["cd"]] = x["v"]
        self._ytd, self._fy, self._q3m = ytd, fy_start, q3m

        self.flow: Dict[str, Dict[str, Dict[str, int]]] = {s: {} for s in FLOW}
        for st in FLOW:
            ends = sorted(ytd[st])
            for i, fim in enumerate(ends):
                start = fy_start[st][fim]
                if q3m[st].get(fim):
                    self.flow[st][fim] = dict(q3m[st][fim])
                elif months_between(start, fim) <= 3:
                    self.flow[st][fim] = dict(ytd[st][fim])
                else:
                    prev = ends[i - 1] if i else None
                    if prev and fy_start[st].get(prev) == start and month_diff(prev, fim) == 3:
                        cur, old = ytd[st][fim], ytd[st][prev]
                        self.flow[st][fim] = {k: v - old.get(k, 0) for k, v in cur.items()}
        self.periods = sorted(set(self.bal) | set(self.flow["DRE"]))

    def serie_por_nome(
        self,
        st: str,
        incluir: str,
        excluir: Optional[str] = None,
        prefixo: str = "",
        so_negativos: bool = False,
        nivel: Optional[int] = None,
        pai: Optional[str] = None,
        ausente_zero: bool = True,
        contas_usadas: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, Optional[int]]:
        """Trimestres isolados da soma das contas cujo *nome* casa, período a período.

        Para contas não fixas (código muda entre ITR/DFP ou entre anos): escolhe
        as contas pelo nome dentro de cada período, soma o acumulado do ano e só
        então diferencia trimestre a trimestre. Trimestre sem o anterior = None.

        nivel: nível máximo do código (2 = "3.11"). pai: regex do nome da conta
        imediatamente acima (ex.: só a parcela dos controladores *do lucro
        líquido*, não a de outra linha). ausente_zero: período sem nenhuma conta
        que case conta como 0 (útil para dividendos, que somem da DFC quando não
        há pagamento); False = None (útil para linhas que sempre existem).
        """
        acum: Dict[str, Optional[int]] = {}
        codes_fim: Dict[str, List[str]] = {}
        for fim, vals in self._ytd[st].items():
            codes = contas_por_nome(self.ds_periodo[(st, fim)], incluir, excluir, prefixo, nivel, pai)
            codes_fim[fim] = codes
            if contas_usadas is not None:
                contas_usadas[fim] = codes
            vs = [vals[cd] for cd in codes if cd in vals and (not so_negativos or vals[cd] < 0)]
            acum[fim] = sum(vs) if (codes or ausente_zero) else None
        out: Dict[str, Optional[int]] = {}
        ends = sorted(acum)
        for i, fim in enumerate(ends):
            start = self._fy[st][fim]
            q3 = self._q3m[st].get(fim, {})
            codes = codes_fim.get(fim, [])
            if acum[fim] is None:
                out[fim] = None
            elif codes and all(cd in q3 for cd in codes):
                # o ITR já traz o trimestre isolado (DRE): usa direto, sem diferenciar
                out[fim] = sum(q3[cd] for cd in codes if not so_negativos or q3[cd] < 0)
            elif months_between(start, fim) <= 3:
                out[fim] = acum[fim]
            else:
                prev = ends[i - 1] if i else None
                ok = prev and self._fy[st].get(prev) == start and month_diff(prev, fim) == 3 and acum[prev] is not None
                out[fim] = acum[fim] - acum[prev] if ok else None  # type: ignore[operator]
        return out

    def saldo_por_nome(
        self,
        st: str,
        incluir: str,
        excluir: Optional[str] = None,
        prefixo: str = "",
        nivel: Optional[int] = None,
        pai: Optional[str] = None,
        contas_usadas: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, Optional[int]]:
        """Saldo (BPA/BPP) no fim de cada período das contas cujo nome casa, período a período."""
        out: Dict[str, Optional[int]] = {}
        for fim in sorted(self.bal):
            nomes = self._ds_bal.get((st, fim), {})
            codes = contas_por_nome(nomes, incluir, excluir, prefixo, nivel, pai)
            if contas_usadas is not None:
                contas_usadas[fim] = codes
            vs = [self.bal[fim][cd] for cd in codes if cd in self.bal[fim]]
            out[fim] = sum(vs) if codes else None
        return out

    def f(self, st: str, fim: str, cd: str) -> Optional[int]:
        return self.flow[st].get(fim, {}).get(cd)

    def b(self, fim: str, cd: str) -> Optional[int]:
        return self.bal.get(fim, {}).get(cd)

    def find(self, st: str, pattern: str, prefix: str = "", max_level: int = 9) -> List[str]:
        rx = re.compile(pattern, re.I)
        return sorted(
            cd
            for cd, ds in self.labels[st].items()
            if cd.startswith(prefix) and cd.count(".") + 1 <= max_level and rx.search(ds)
        )


def contas_por_nome(
    nomes: Dict[str, str],
    incluir: str,
    excluir: Optional[str] = None,
    prefixo: str = "",
    nivel: Optional[int] = None,
    pai: Optional[str] = None,
) -> List[str]:
    """Códigos (só as folhas) cujo nome casa com `incluir` num período (cd -> nome)."""
    inc = re.compile(incluir, re.I)
    exc = re.compile(excluir, re.I) if excluir else None
    pai_rx = re.compile(pai, re.I) if pai else None
    cands = []
    for cd, ds in nomes.items():
        if not cd.startswith(prefixo) or not inc.search(ds) or (exc and exc.search(ds)):
            continue
        if nivel is not None and cd.count(".") + 1 > nivel:
            continue
        if pai_rx is not None and not pai_rx.search(nomes.get(cd.rsplit(".", 1)[0], "")):
            continue
        cands.append(cd)
    return leaves_only(cands)


def leaves_only(codes: List[str]) -> List[str]:
    """Remove códigos que têm um descendente também na lista (evita contar duas vezes)."""
    return [c for c in codes if not any(o != c and o.startswith(c + ".") for o in codes)]


def load(ident: str, trimestres: int, individual: bool):
    info = resolve(ident)
    cnpj = info["CNPJ_CIA"]
    consol = "ind" if individual else "con"
    this_year = time.localtime().tm_year
    # trimestres exibidos + 4 anteriores (a/a e LTM), a partir do último trimestre publicado
    years = range(this_year - (trimestres + 4 + 3) // 4, this_year + 1)
    linhas: List[dict] = []
    pareceres: List[dict] = []
    for y in years:
        for doc in ("itr", "dfp"):
            ls, ps = load_doc_year(doc, y, cnpj, consol)
            linhas.extend(ls)
            pareceres.extend(ps)
    if not linhas and not individual:
        warn("sem demonstrações consolidadas; usando individuais")
        return load(ident, trimestres, True)
    if not linhas:
        die("nenhuma demonstração ITR/DFP encontrada para essa empresa no período")
    return info, Dados(linhas), pareceres, consol


# ---------------------------------------------------------------- resumo


def ltm(series: List[Optional[int]], i: int) -> Optional[int]:
    if i < 3:
        return None
    window = series[i - 3 : i + 1]
    return None if any(v is None for v in window) else sum(window)  # type: ignore[arg-type]


def cmd_resumo(ident: str, trimestres: int, individual: bool) -> None:
    info, d, pareceres, consol = load(ident, trimestres, individual)
    header(info)
    ends = [p for p in d.periods if p in d.flow["DRE"]]
    if not ends:
        die("sem DRE trimestral")

    rec_label = d.labels["DRE"].get("3.01", "")
    # plano de banco ("Intermediação Financeira") ou de seguradora/holding de seguros
    # ("Atividades Seguradoras", "Receitas das Operações"): reconhece pelas contas de nível 2
    nivel2 = " | ".join(ds for cd, ds in d.labels["DRE"].items() if cd.count(".") == 1)
    # seguradoras no plano comercial (ex.: Porto) têm prêmios dentro da receita (3.01.xx)
    todas_dre = " | ".join(d.labels["DRE"].values())
    financeira = bool(
        re.search(r"intermedia|prêmios|seguros", rec_label, re.I)
        or re.search(r"intermedia[çc][ãa]o financeira|atividades? segurador|resseguradora|sinistros", nivel2, re.I)
        or re.search(r"pr[êe]mios de seguros|receita de seguro|contrapresta[çc][õo]es l[íi]quidas", todas_dre, re.I)
    )

    receita = [d.f("DRE", e, "3.01") for e in ends]
    # contas localizadas pelo nome no nível 2: funciona para o plano de empresas
    # comerciais e para o de bancos/seguradoras (códigos diferentes)
    # contas localizadas pelo nome, no nível 2 e *dentro de cada período*:
    # funciona para o plano de empresas comerciais e o de bancos/seguradoras, e
    # para empresas cujo código muda entre ITR e DFP (ex.: lucro dos
    # controladores da Sabesp)
    def dre(pattern: str, **kw) -> List[Optional[int]]:
        serie = d.serie_por_nome("DRE", pattern, prefixo="3.", ausente_zero=False, **kw)
        return [serie.get(e) for e in ends]

    bruto = dre(r"^resultado bruto", nivel=2)
    ebit = dre(r"^resultado antes do resultado financeiro", nivel=2)
    fin = dre(r"^resultado financeiro", nivel=2)
    lair = dre(r"^resultado antes dos tributos", nivel=2)
    ir = dre(r"^imposto de renda e contribui", nivel=2)
    ll = dre(LL_RX, nivel=2)
    ll_ctrl = dre(r"controlador", excluir=r"n[ãa]o\s+controlador", nivel=3, pai=LL_RX)
    # nível 2 no plano de seguradora (BB Seguridade: 3.06), nível 3 no comercial (Caixa Seguridade: 3.04.06)
    equiv = dre(r"^resultado d[ae] equival[êe]ncia patrimonial", nivel=3)
    # empresas que preenchem a divisão controladores/minoritários com 0 (ex.: Sabesp
    # até 1T26): 0 com lucro total diferente de 0 é "não informado", não zero
    ctrl_zerado = [i for i, (c, t) in enumerate(zip(ll_ctrl, ll)) if c == 0 and t not in (None, 0)]
    for i in ctrl_zerado:
        ll_ctrl[i] = None

    da_codes = leaves_only(d.find("DVA", r"^deprecia|amortiza[çc][ãa]o e exaust", "7."))[:1]
    da = [(abs(d.f("DVA", e, da_codes[0]) or 0) if da_codes and d.f("DVA", e, da_codes[0]) is not None else None) for e in ends]
    ebitda = [None if a is None or b is None else a + b for a, b in zip(ebit, da)]

    fco = [d.f("DFC", e, "6.01") for e in ends]
    capex_rx = r"imobilizad|intang"
    capex_serie = d.serie_por_nome("DFC", capex_rx, r"venda|aliena|baixa", "6.02", so_negativos=True)
    capex = [capex_serie.get(e) for e in ends]
    fcl = [None if a is None or b is None else a + b for a, b in zip(fco, capex)]

    def bal_sum(e: str, codes: List[str]) -> Optional[int]:
        vals = [d.b(e, c) for c in codes]
        vals = [v for v in vals if v is not None]
        return sum(vals) if vals else None

    div_codes = [c for c in ("2.01.04", "2.02.01") if re.search(r"empr[ée]stimo", d.labels["BPP"].get(c, ""), re.I)]
    caixa = [bal_sum(e, ["1.01.01", "1.01.02"]) for e in ends]
    divida = [bal_sum(e, div_codes) if div_codes else None for e in ends]
    dl = [None if a is None or b is None else a - b for a, b in zip(divida, caixa)]
    pl_codes = d.find("BPP", r"^patrim[ôo]nio l[íi]quido", "2.", max_level=2)
    pl = [d.b(e, pl_codes[0]) if pl_codes else None for e in ends]
    ac = [d.b(e, "1.01") for e in ends]
    pc = [d.b(e, "2.01") for e in ends]

    idx = list(range(len(ends)))
    show = idx[-trimestres:]
    cols = [quarter_label(ends[i]) for i in show] + ["LTM"]
    last = idx[-1]

    def row_money(name: str, s: List[Optional[int]], flow: bool = True) -> List[str]:
        return [name] + [fmt_mi(s[i]) for i in show] + [fmt_mi(ltm(s, last)) if flow else fmt_mi(s[last])]

    def row_ratio(name: str, fn, ltm_fn=None) -> List[str]:
        return [name] + [fmt_pct(fn(i)) for i in show] + [fmt_pct(ltm_fn()) if ltm_fn else "-"]

    # crescimento e razões só com base positiva: sobre base negativa o % engana
    def yoy(s, i):
        return div(s[i] - s[i - 4], s[i - 4]) if i >= 4 and s[i] is not None and (s[i - 4] or 0) > 0 else None

    def qoq(s, i):
        return div(s[i] - s[i - 1], s[i - 1]) if i >= 1 and s[i] is not None and (s[i - 1] or 0) > 0 else None

    def pos_div(a, b):
        return div(a, b) if a is not None and b is not None and b > 0 else None

    rows: List[List[str]] = []
    sem_receita = all(v in (None, 0) for v in receita[-trimestres:])
    if not sem_receita:
        rows.append(row_money("Receita (3.01)", receita))
        rows.append(row_ratio("  cresc. a/a", lambda i: yoy(receita, i)))
        rows.append(row_ratio("  cresc. t/t", lambda i: qoq(receita, i)))
    # holding (ex.: BB Seguridade, Caixa Seguridade): o lucro vem das investidas
    # critério duplo: equivalência relevante no lucro *e* maior parte do resultado
    # operacional (EBIT inclui a equivalência no plano comercial). Só o lucro não basta:
    # empresa operacional com lucro quase zero e uma joint venture (ex.: Magalu) passaria.
    eq_ltm = ltm(equiv, last)
    holding = any(v for v in equiv[-trimestres:]) and (
        sem_receita
        or ((pos_div(eq_ltm, ltm(ll, last)) or 0) >= 0.3 and (pos_div(eq_ltm, ltm(ebit, last)) or 0) >= 0.5)
    )
    if holding:
        rows.append(row_money("Equivalência patrimonial", equiv))
        rows.append(row_ratio("  % do lucro líquido", lambda i: pos_div(equiv[i], ll[i]), lambda: pos_div(ltm(equiv, last), ltm(ll, last))))
    if (financeira or holding) and any(v is not None for v in fin[-trimestres:]):
        rows.append(row_money("Resultado financeiro", fin))
    # margens/EBITDA não se aplicam a financeiras nem a holdings (lucro vem das investidas)
    operacional = not financeira and not holding
    if operacional:
        rows.append(row_ratio("Margem bruta", lambda i: div(bruto[i], receita[i]), lambda: div(ltm(bruto, last), ltm(receita, last))))
        rows.append(row_money("EBIT", ebit))
        rows.append(row_ratio("Margem EBIT", lambda i: div(ebit[i], receita[i]), lambda: div(ltm(ebit, last), ltm(receita, last))))
        rows.append(row_money("D&A (DVA)", da))
        rows.append(row_money("EBITDA (EBIT+D&A)", ebitda))
        rows.append(row_ratio("Margem EBITDA", lambda i: div(ebitda[i], receita[i]), lambda: div(ltm(ebitda, last), ltm(receita, last))))
        rows.append(row_money("Resultado financeiro", fin))
    rows.append(row_money("IR/CS", ir))
    rows.append(row_ratio("Alíquota efetiva", lambda i: pos_div(-ir[i], lair[i]) if ir[i] is not None else None,
                          lambda: pos_div(-(ltm(ir, last) or 0), ltm(lair, last))))
    rows.append(row_money("Lucro líquido", ll))
    rows.append(row_ratio("  cresc. a/a", lambda i: yoy(ll, i)))
    rows.append(row_ratio("Margem líquida", lambda i: div(ll[i], receita[i]), lambda: div(ltm(ll, last), ltm(receita, last))))
    if any(v is not None for v in ll_ctrl):
        rows.append(row_money("LL controladores", ll_ctrl))
    rows.append(row_money("FCO", fco))
    if operacional:
        rows.append(row_money("Capex (imob.+intang.)", capex))
        rows.append(row_money("FCL (FCO+capex)", fcl))
    # em banco/seguradora o FCO mistura captação, crédito e reservas; em holding não inclui os
    # dividendos recebidos das investidas: nos dois casos a razão não mede qualidade do lucro
    if operacional:
        rows.append(row_ratio("FCO/Lucro líquido", lambda i: pos_div(fco[i], ll[i]), lambda: pos_div(ltm(fco, last), ltm(ll, last))))
    if not financeira:
        rows.append(row_money("Caixa+aplic. CP", caixa, flow=False))
        rows.append(row_money("Dívida bruta (empr./fin.)", divida, flow=False))
        rows.append(row_money("Dívida líquida", dl, flow=False))
        if operacional:  # em holding o EBITDA é basicamente equivalência patrimonial
            rows.append(
                ["DL/EBITDA LTM"]
                + [fmt_num(div(dl[i], ltm(ebitda, i)), 2) + "x" if div(dl[i], ltm(ebitda, i)) is not None else "-" for i in show]
                + ["-"]
            )
        rows.append(
            ["Liquidez corrente"]
            + [fmt_num(div(ac[i], pc[i]), 2) if div(ac[i], pc[i]) is not None else "-" for i in show]
            + ["-"]
        )
    rows.append(row_money("Patrimônio líquido", pl, flow=False))
    rows.append(row_ratio("ROE LTM (LL/PL fim)", lambda i: pos_div(ltm(ll, i), pl[i])))

    print(f"\nDemonstrações {'consolidadas' if consol == 'con' else 'individuais'}, R$ milhões, trimestres isolados:")
    print_table(["Indicador"] + cols, rows)
    notas = [
        "EBITDA = EBIT (3.05) + D&A da DVA; não é o 'EBITDA ajustado' do release.",
        "Dívida bruta = empréstimos e financiamentos CP+LP (2.01.04 + 2.02.01); arrendamentos (IFRS 16) e risco sacado podem estar fora — confira notas explicativas.",
        "Capex = saídas em contas da DFC (6.02) com imobilizado/intangível no nome, escolhidas período a período (códigos dessas contas mudam entre ITR e DFP).",
    ]
    if financeira:
        notas = [
            "Plano de contas de instituição financeira/seguradora: EBITDA, dívida líquida e margens não se aplicam; use o release para NPL, Basileia, sinistralidade, índice combinado etc.",
            "FCO/Lucro líquido omitido: em banco/seguradora o FCO reflete captação, crédito e reservas, não a qualidade do lucro.",
        ]
    if holding:
        notas.append(
            "Holding: o lucro vem da equivalência patrimonial das investidas; os dividendos que ela recebe entram no "
            "fluxo de investimento, não no FCO (veja `contas TICKER --nome \"dividend\" --prefixo 6.02`)."
        )
    if any(i >= len(ends) - trimestres for i in ctrl_zerado):
        notas.append(
            "LL controladores '-' em trimestres em que a empresa informou 0 para a divisão controladores/minoritários "
            "com lucro total diferente de 0 (campo não preenchido); use o lucro total."
        )
    if any(v is not None and v > 0 for v in ir[-trimestres:]):
        notas.append(
            "Alíquota negativa = IR/CS positivo na DRE (crédito tributário, ex.: JCP, diferidos): o imposto *aumentou* o lucro. "
            "Veja quanto do lucro vem disso comparando IR/CS com o lucro líquido."
        )
    for n in notas:
        print(f"- {n}")

    if pareceres:
        vistos = resumir_pareceres(pareceres)
        print("\nAuditor por período: " + " | ".join(list(vistos.values())[-trimestres:]))
    print("Fonte: CVM Dados Abertos (ITR/DFP/FCA/cadastro).")


GRAVIDADE_PARECER = ["adverso", "negativa", "abstenção", "com ressalva", "sem ressalva"]


def resumir_pareceres(pareceres: List[dict]) -> Dict[str, str]:
    """Uma descrição por período, combinando todas as linhas de parecer dele.

    Algumas empresas têm mais de uma linha por período na CVM (ex.: BB, com a
    ênfase numa linha e outra sem): vale o pior tipo de parecer e somam-se as
    ênfases e a incerteza de continuidade de todas as linhas.
    """
    por_ref: Dict[str, List[dict]] = defaultdict(list)
    for p in pareceres:
        por_ref[p["ref"]].append(p)

    def gravidade(tipo: str) -> int:
        t = tipo.lower()
        return next((i for i, g in enumerate(GRAVIDADE_PARECER) if g in t), len(GRAVIDADE_PARECER))

    out: Dict[str, str] = {}
    for ref in sorted(por_ref):
        ps = por_ref[ref]
        tipo = min((p["tipo"] for p in ps), key=gravidade)
        temas = sorted({(p.get("enfase_tema") or "").strip()[:60] for p in ps if p["enfase"]})
        flag = []
        if temas:
            nomeados = [t for t in temas if t]
            flag.append("ênfase: " + "; ".join(nomeados) if nomeados else "com parágrafo de ênfase")
        if any(p["incerteza"] for p in ps):
            flag.append("incerteza relevante sobre continuidade")
        out[ref] = f"{ref[:7]} {tipo}" + (f" ({'; '.join(flag)})" if flag else "")
    return out


# ---------------------------------------------------------- contas/plano


PREFIXO_ST = {"BPA": "1", "BPP": "2", "DRE": "3", "DFC": "6", "DVA": "7"}


def cmd_contas(
    ident: str,
    codigos: List[str],
    trimestres: int,
    individual: bool,
    nome: Optional[str] = None,
    excluir: Optional[str] = None,
    demonstracao: Optional[str] = None,
    nivel: Optional[int] = None,
    prefixo: Optional[str] = None,
) -> None:
    info, d, _, consol = load(ident, trimestres, individual)
    header(info)
    ends = d.periods[-trimestres:]
    rows = []
    if nome:
        # contas escolhidas pelo nome dentro de cada período (contas não fixas mudam de código)
        if prefixo:
            st_pref = next((st for st, raiz in PREFIXO_ST.items() if prefixo.split(".")[0] == raiz), None)
            sts = [st_pref] if st_pref else []
        elif demonstracao:
            sts = [demonstracao.upper().replace("DFC_MI", "DFC").replace("DFC_MD", "DFC")]
        else:
            sts = list(PREFIXO_ST)
        detalhes: List[str] = []
        avisos: List[str] = []
        for st in sts:
            pref = prefixo or PREFIXO_ST[st]
            usadas: Dict[str, List[str]] = {}
            if st in ("BPA", "BPP"):
                serie = d.saldo_por_nome(st, nome, excluir, pref, nivel, contas_usadas=usadas)
            else:
                serie = d.serie_por_nome(st, nome, excluir, pref, nivel=nivel, ausente_zero=False, contas_usadas=usadas)
            if not any(usadas.get(e) for e in ends):
                continue
            rows.append([st, f"soma: /{nome}/" + (f" exceto /{excluir}/" if excluir else "")] + [fmt_mi(serie.get(e)) for e in ends])
            rows.append(["", "nº de contas"] + [str(len(usadas.get(e) or [])) for e in ends])
            grupos = set()
            for e in ends:
                nomes = d._ds_bal.get((st, e), {}) if st in ("BPA", "BPP") else d.ds_periodo.get((st, e), {})
                cods = usadas.get(e) or []
                grupos.update(".".join(cd.split(".")[:2]) for cd in cods)
                detalhes.append(
                    f"{st} {quarter_label(e)}: "
                    + ("; ".join(f"{cd} {nomes.get(cd, '')[:45]}" for cd in cods) if cods else "(nenhuma)")
                )
            if len(grupos) > 1:
                avisos.append(
                    f"{st}: as contas casadas estão em grupos diferentes ({', '.join(sorted(grupos))}) — a soma pode "
                    f"misturar coisas distintas (ex.: dividendos recebidos x pagos). Restrinja com --prefixo ou --excluir."
                )
        if not rows:
            die(f"nenhuma conta com nome /{nome}/ nos períodos; veja `plano {ident} --demonstracao ...`")
        print_table(["Demonstr.", "Conta"] + [quarter_label(e) for e in ends], rows)
        print(
            "R$ milhões; DRE/DFC/DVA = trimestre isolado (contas escolhidas pelo nome em cada período); "
            "BPA/BPP = saldo no fim do período."
        )
        for a in avisos:
            print(f"AVISO: {a}")
        print("Contas usadas por período:")
        for linha_det in detalhes:
            print(f"- {linha_det}")
        return
    for cd in codigos:
        st = next((s for s in ("BPA", "BPP", "DRE", "DFC", "DVA") if cd in d.labels[s]), None)
        if st is None:
            rows.append([cd, "(não encontrado)"] + ["-"] * len(ends))
            continue
        vals = [d.b(e, cd) if st in ("BPA", "BPP") else d.f(st, e, cd) for e in ends]
        rows.append([cd, f"{st}: {d.labels[st][cd][:40]}"] + [fmt_mi(v) for v in vals])
    print_table(["Código", "Conta"] + [quarter_label(e) for e in ends], rows)
    print("R$ milhões; DRE/DFC/DVA = trimestre isolado; BPA/BPP = saldo no fim do período.")


def cmd_plano(ident: str, demonstracao: str, nivel: int, individual: bool) -> None:
    info, d, _, _ = load(ident, 1, individual)
    header(info)
    st = demonstracao.upper().replace("DFC_MI", "DFC").replace("DFC_MD", "DFC")
    for cd, ds in sorted(d.labels.get(st, {}).items(), key=lambda kv: [int(x) for x in kv[0].split(".") if x.isdigit()]):
        if cd.count(".") + 1 <= nivel:
            print(f"{cd} {ds}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("resumo")
    p.add_argument("empresa")
    p.add_argument("--trimestres", type=int, default=8)
    p.add_argument("--individual", action="store_true")
    p = sub.add_parser("contas")
    p.add_argument("empresa")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--codigos", help="ex.: 3.01,3.04.02,2.01.04 (código literal; cuidado com contas não fixas)")
    g.add_argument("--nome", help='regex no nome da conta, escolhida período a período (ex.: "dividend|juros sobre o capital")')
    p.add_argument("--excluir", help='regex de nomes a excluir (ex.: "n[ãa]o controlador")')
    p.add_argument("--demonstracao", help="com --nome: BPA, BPP, DRE, DFC ou DVA (padrão: todas)")
    p.add_argument("--nivel", type=int, help="com --nome: nível máximo do código (2 = '3.11')")
    p.add_argument("--prefixo", help="com --nome: só contas sob este código (ex.: 6.03 = fluxo de financiamento)")
    p.add_argument("--trimestres", type=int, default=8)
    p.add_argument("--individual", action="store_true")
    p = sub.add_parser("plano")
    p.add_argument("empresa")
    p.add_argument("--demonstracao", default="DRE", help="BPA, BPP, DRE, DFC, DVA")
    p.add_argument("--nivel", type=int, default=3)
    p.add_argument("--individual", action="store_true")
    p = sub.add_parser("pares")
    p.add_argument("empresa")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--setor", help="sobrescreve o setor da CVM (ex.: \"Energia Elétrica\"); útil para holdings \"Sem Setor Principal\"")
    p = sub.add_parser("resolver")
    p.add_argument("empresa")
    args = ap.parse_args()

    if args.cmd == "resumo":
        cmd_resumo(args.empresa, args.trimestres, args.individual)
    elif args.cmd == "contas":
        codigos = [c.strip() for c in (args.codigos or "").split(",") if c.strip()]
        cmd_contas(
            args.empresa, codigos, args.trimestres, args.individual, args.nome, args.excluir, args.demonstracao, args.nivel, args.prefixo
        )
    elif args.cmd == "pares":
        cmd_pares(args.empresa, args.top, args.setor)
    elif args.cmd == "plano":
        cmd_plano(args.empresa, args.demonstracao, args.nivel, args.individual)
    else:
        header(resolve(args.empresa))


if __name__ == "__main__":
    sys.exit(main())
