#!/usr/bin/env python3
"""Lista e baixa documentos (PDF) de FIIs (FundosNET/B3) e de companhias (IPE/CVM).

Uso:
  documentos.py fii HGLG11 [--tipo relatorio] [-n 10] [--baixar 2] [--ids 1307338,1299001]
      --tipo: relatorio | fato | rendimento | informe | assembleia | todos (padrão relatorio)
  documentos.py cia PETR4 [--tipo release] [-n 10] [--baixar 1] [--ids 1094451]
      --tipo: release | fato | comunicado | apresentacao | dfs | assembleia | proventos | todos
  --busca TEXTO filtra adicionalmente por texto no tipo/assunto.

Duplicatas: por padrão a lista traz um documento por período e sempre o mais
recente. Tipos periódicos (release, dfs, relatorio, informe) ficam com um
documento por trimestre (cia) ou mês (fii); entre candidatos do mesmo
período, prefere português a inglês, depois assunto de release/resultado
(em vez de, ex., relatório da administração) e, por fim, a entrega mais
recente (reapresentações substituem a original). Nos demais tipos, o mesmo
documento reapresentado (mesmo assunto e referência) aparece uma vez só, na
versão mais recente. --todas-versoes desliga isso. -n conta documentos já
deduplicados, então "-n 3 --baixar 3" = últimos 3 trimestres.

A listagem é compacta (uma linha por documento, com o id). --baixar N baixa os
N primeiros da lista; --ids baixa ids específicos, mesmo fora da lista
(no caso de empresa, qualquer documento do índice IPE dos últimos 5 anos,
de qualquer tipo). PDFs vão para
.cache/analise-fii-acoes/docs/<TICKER>/ e o caminho é impresso — depois use
pdf_texto.py neles.

FundosNET não é API oficial (pode mudar sem aviso): o script espera ~1 s entre
requisições. O índice do IPE vem do CVM Dados Abertos (ZIP anual, cacheado).
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import time
import unicodedata
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional

from _comum import (
    HttpError,
    cache_path,
    cvm_max_age,
    die,
    download_cached,
    http_get,
    json_cache_get,
    json_cache_put,
    iter_zip_csv,
    only_digits,
    warn,
)

FNET = "https://fnet.bmfbovespa.com.br/fnet/publico"
IPE_BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS"

FII_TIPOS = {
    "relatorio": r"relat[óo]rio gerencial",
    "fato": r"fato relevante",
    "rendimento": r"rendimento|amortiza|aviso aos cotistas",
    "informe": r"informe",
    "assembleia": r"assembl|edital|ata |proposta|consulta formal",
    "todos": r".",
}
CIA_TIPOS = {
    "release": r"press-release|release de resultado|relat[óo]rio de an[áa]lise gerencial|an[áa]lise d[oe] desempenho|relat[óo]rio de desempenho",
    "fato": r"fato relevante",
    "comunicado": r"comunicado ao mercado",
    "apresentacao": r"apresenta[çc][õo]es a analistas|apresenta",
    "dfs": r"demonstra[çc][õo]es financeiras",
    "assembleia": r"assembleia|\bago\b|\bage\b",
    "proventos": r"aviso aos acionistas|proventos",
    "todos": r".",
}
# tipos com um documento por período (trimestre na cia, mês no fii)
CIA_PERIODICOS = {"release", "dfs"}
FII_PERIODICOS = {"relatorio", "informe"}

INGLES = re.compile(r"ingl[êe]s|english|\b[1-4]Q\d{2}\b|\bEN\b|earnings release", re.I)
RELEASE = re.compile(r"release|resultado|desempenho|earnings", re.I)
# relatório completo de resultados (MD&A): preferido ao release de imprensa curto
MDA = re.compile(r"an[áa]lise d[oe] desempenho|relat[óo]rio de an[áa]lise gerencial|relat[óo]rio de desempenho|md&a", re.I)
MENSAL = re.compile(r"mensal", re.I)


def quarter_key(date_iso: str) -> str:
    """"2026-03-30" -> "2026T1" (datas de referência irregulares caem no trimestre certo)."""
    if len(date_iso) < 7 or not date_iso[:4].isdigit():
        return date_iso
    return f"{date_iso[:4]}T{(int(date_iso[5:7]) - 1) // 3 + 1}"


def entrega_fnet(s: str) -> str:
    """"15/09/2026 20:03" -> "2026-09-15 20:03" (ordenável)."""
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})\s*(.*)", s or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)} {m.group(4)}" if m else (s or "")


def dedupe(docs: List[dict], key_fn, rank_fn) -> List[dict]:
    """Um documento por chave: o de maior rank (preferência + entrega mais recente).

    Preserva a ordem de aparição da chave pelo documento escolhido (ordenado por
    entrega desc) e anota em `_omitidos` quantas duplicatas foram descartadas.
    """
    grupos: Dict[str, List[dict]] = {}
    for d in docs:
        grupos.setdefault(key_fn(d), []).append(d)
    out = []
    for grupo in grupos.values():
        grupo.sort(key=rank_fn, reverse=True)
        best = dict(grupo[0])
        best["_omitidos"] = len(grupo) - 1
        out.append(best)
    out.sort(key=rank_fn, reverse=True)
    out.sort(key=lambda d: d.get("_ordem", ""), reverse=True)
    return out


def omitidos(d: dict) -> str:
    k = d.get("_omitidos", 0)
    return f" | +{k} versão(ões)/duplicata(s) omitida(s)" if k else ""


def slug(s: str, n: int = 40) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:n] or "doc"


def iso_ref(ref: str) -> str:
    """"31/08/2026" ou "08/2026" -> "20260831" / "202608" (ordena por nome)."""
    parts = [p for p in re.split(r"[^0-9]", ref) if p]
    return "".join(reversed(parts)) or "semdata"


def save_pdf(data: bytes, dest: Path) -> Path:
    # FundosNET às vezes devolve o PDF em base64 no corpo
    if not data.startswith(b"%PDF"):
        try:
            decoded = base64.b64decode(data, validate=False)
            if decoded.startswith(b"%PDF"):
                data = decoded
        except Exception:  # noqa: BLE001
            pass
    if not data.startswith(b"%PDF"):
        dest = dest.with_suffix(".html" if b"<html" in data[:2000].lower() else ".bin")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest


# --------------------------------------------------------------------- FII


def fnet_page(cnpj_digits: str, i: int, page: int) -> List[dict]:
    """Uma página da busca do FundosNET, com cache de 30 min (o servidor oscila muito)."""
    cp = cache_path("fnet", f"{cnpj_digits}_{i}_{page}.json")
    cached = json_cache_get(cp, 30 * 60)
    if cached is not None:
        return cached
    params = {
        "d": str(i + 1),
        "s": str(i * page),
        "l": str(page),
        "o[0][dataEntrega]": "desc",
        "cnpjFundo": cnpj_digits,
    }
    url = f"{FNET}/pesquisarGerenciadorDocumentosDados?" + urllib.parse.urlencode(params)
    docs = json.loads(http_get(url, timeout=25, retries=4).decode("utf-8")).get("data") or []
    json_cache_put(cp, docs)
    return docs


def tipo_fnet(d: dict) -> str:
    """Fato relevante vem com tipoDocumento vazio e o nome na categoria."""
    return (d.get("tipoDocumento") or "").strip() or (d.get("categoriaDocumento") or "").strip()


def fnet_meta(cnpj_digits: str, doc_id: str) -> Optional[dict]:
    """Dados de um documento nas páginas da busca já em cache (sem nova requisição)."""
    for cp in sorted(cache_path("fnet", "x").parent.glob(f"{cnpj_digits}_*_*.json")):
        try:
            for d in json.loads(cp.read_text(encoding="utf-8")):
                if str(d.get("id")) == str(doc_id):
                    return d
        except (OSError, ValueError):
            continue
    return None


def fnet_dedupe(docs: List[dict], periodico: bool) -> List[dict]:
    for d in docs:
        ref = iso_ref(d.get("dataReferencia", ""))
        d["_ordem"] = ref[:6] if periodico else entrega_fnet(d.get("dataEntrega", ""))
    if periodico:
        key = lambda d: f"{tipo_fnet(d).lower()}|{d['_ordem']}"  # noqa: E731
    else:
        key = lambda d: f"{tipo_fnet(d).lower()}|{d.get('dataReferencia')}|{d.get('especieDocumento')}"  # noqa: E731
    return dedupe(docs, key, lambda d: (entrega_fnet(d.get("dataEntrega", "")), int(d.get("versao") or 0), int(d["id"])))


def fnet_search(cnpj_digits: str, pattern: str, busca: Optional[str], n: int, periodico: bool, todas: bool) -> List[dict]:
    rx = re.compile(pattern, re.I)
    out: List[dict] = []
    page = 100
    for i in range(5):
        if i:
            time.sleep(1)
        try:
            docs = fnet_page(cnpj_digits, i, page)
        except (OSError, HttpError) as e:
            die(f"FundosNET não respondeu ({e}); o serviço oscila bastante, tente de novo em alguns minutos")
        for d in docs:
            texto = f"{d.get('categoriaDocumento', '')} {d.get('tipoDocumento', '')} {d.get('especieDocumento', '')}"
            if d.get("descricaoStatus", "").lower().startswith("inativo"):
                continue  # versão substituída por reapresentação
            if rx.search(texto) and (not busca or busca.lower() in texto.lower()):
                out.append(d)
        # para quando já há n documentos distintos (a próxima página pode
        # trazer duplicatas antigas do último período, então confere após a página)
        if (len(out) if todas else len(fnet_dedupe(list(out), periodico))) >= n + 1 or len(docs) < page:
            break
    if todas:
        return out[:n]
    return fnet_dedupe(out, periodico)[:n]


def cmd_fii(ticker: str, tipo: str, busca: Optional[str], n: int, baixar: int, ids: List[str], todas: bool) -> None:
    from cvm_fii import resolve

    g = resolve(ticker)
    cnpj = only_digits(g["CNPJ_Fundo_Classe"])
    periodico = tipo in FII_PERIODICOS
    docs = fnet_search(cnpj, FII_TIPOS[tipo], busca, n, periodico, todas)
    modo = "todas as versões" if todas else ("1 por mês, a mais recente" if periodico else "sem reapresentações repetidas")
    print(f"{g['Nome_Fundo_Classe']} (CNPJ {g['CNPJ_Fundo_Classe']}) — FundosNET, mais recentes primeiro ({modo}):")
    for d in docs:
        print(
            f"id={d['id']} | ref {d.get('dataReferencia', '')} | entregue {d.get('dataEntrega', '')} | "
            f"{tipo_fnet(d)} | {d.get('descricaoModalidade', '')}{omitidos(d)}"
        )
    if not docs:
        print("(nenhum documento com esse filtro)")
    if ids:
        # qualquer id: usa os dados da listagem ou das páginas já consultadas do
        # FundosNET; sem dados, baixa direto pelo id (nome de arquivo genérico)
        listados = {str(d["id"]): d for d in docs}
        alvo = [listados.get(i) or fnet_meta(cnpj, i) or {"id": int(i), "tipoDocumento": "documento"} for i in ids]
    else:
        alvo = docs[:baixar]
    for i, d in enumerate(alvo):
        if i:
            time.sleep(1)
        ref = iso_ref(d.get("dataReferencia", ""))
        dest = cache_path("docs", ticker.upper(), f"{ref}_{slug(tipo_fnet(d))}_{d['id']}.pdf")
        if not dest.exists():
            dest = save_pdf(http_get(f"{FNET}/downloadDocumento?id={d['id']}", timeout=120), dest)
        print(f"baixado: {dest}")


# --------------------------------------------------------------------- CIA


def ipe_rank(r: dict, tipo: str):
    """Preferência entre candidatos do mesmo período: PT > EN, relatório completo de
    desempenho > release de resultado > outros, entrega mais recente."""
    assunto = r.get("Assunto") or ""
    texto = f"{r.get('Tipo', '')} {assunto}"
    if tipo != "release":
        pref = 1
    else:
        pref = 2 if MDA.search(texto) else 1 if RELEASE.search(assunto) else 0
    return (
        0 if INGLES.search(assunto) else 1,
        pref,
        r.get("Data_Entrega", ""),
        int(r.get("Versao") or 0),
        int(r.get("_id") or 0),
    )


def ipe_dedupe(docs: List[dict], tipo: str) -> List[dict]:
    periodico = tipo in CIA_PERIODICOS
    for r in docs:
        r["_ordem"] = quarter_key(r.get("Data_Referencia", "")) if periodico else r.get("Data_Entrega", "")
    if periodico:
        key = lambda r: r["_ordem"]  # noqa: E731
    else:
        key = lambda r: f"{r.get('Categoria')}|{r.get('Tipo')}|{(r.get('Assunto') or '').strip().lower()}|{r.get('Data_Referencia')}"  # noqa: E731
    return dedupe(docs, key, lambda r: ipe_rank(r, tipo))


def cmd_cia(ticker: str, tipo: str, busca: Optional[str], n: int, baixar: int, ids: List[str], todas: bool) -> None:
    from cvm_cia import resolve

    info = resolve(ticker)
    cnpj = info["CNPJ_CIA"]
    rx = re.compile(CIA_TIPOS[tipo], re.I)
    this_year = time.localtime().tm_year
    docs: List[dict] = []
    por_id: Dict[str, dict] = {}  # todos os documentos da empresa, de qualquer tipo (para --ids)
    # ano corrente e anterior; recua até 5 anos se ainda faltarem documentos (ex.: -n 8)
    # ou algum id pedido em --ids
    for k, y in enumerate(range(this_year, this_year - 5, -1)):
        name = f"ipe_cia_aberta_{y}.zip"
        z = download_cached(f"{IPE_BASE}/{name}", cache_path("cvm", "cia", name), cvm_max_age(y))
        if z is not None:
            for r in iter_zip_csv(z, f"ipe_cia_aberta_{y}.csv", lambda line: line.startswith(cnpj)):
                qs = urllib.parse.urlparse(r["Link_Download"].strip()).query
                r["_id"] = dict(urllib.parse.parse_qsl(qs)).get("numSequencia", "")
                por_id[r["_id"]] = r
                texto = f"{r.get('Categoria', '')} {r.get('Tipo', '')} {r.get('Especie', '')} {r.get('Assunto', '')}"
                if not rx.search(texto) or (busca and busca.lower() not in texto.lower()):
                    continue
                if tipo in CIA_PERIODICOS and (
                    not (r.get("Categoria") or "").lower().startswith("dados econ")
                    or MENSAL.search(r.get("Assunto") or "")
                ):
                    # release/DFs periódicos só na categoria de dados econômico-financeiros: a
                    # versão em inglês costuma vir como "Comunicado ao Mercado" com data do
                    # trimestre seguinte, e informativos mensais não são release trimestral
                    continue
                docs.append(r)
        distintos = len(docs) if todas else len(ipe_dedupe([dict(d) for d in docs], tipo))
        faltam_ids = [i for i in ids if i not in por_id]
        if k >= 1 and distintos > n and not faltam_ids:
            break
    if todas:
        docs.sort(key=lambda r: (r.get("Data_Entrega", ""), int(r.get("_id") or 0)), reverse=True)
        docs = docs[:n]
    else:
        docs = ipe_dedupe(docs, tipo)[:n]

    modo = "todas as versões" if todas else (
        "1 por trimestre: PT, relatório de desempenho > release, entrega mais recente"
        if tipo in CIA_PERIODICOS
        else "sem reapresentações repetidas"
    )
    print(f"{info.get('DENOM_SOCIAL', cnpj)} — IPE/CVM, mais recentes primeiro ({modo}):")
    for r in docs:
        assunto = (r.get("Assunto") or "").replace("\n", " ")[:90]
        print(
            f"id={r['_id']} | ref {r.get('Data_Referencia', '')} | entregue {r.get('Data_Entrega', '')} | "
            f"{r.get('Categoria', '')[:35]} / {r.get('Tipo', '')[:35]}" + (f" | {assunto}" if assunto else "") + omitidos(r)
        )
    if not docs:
        print("(nenhum documento com esse filtro)")
    if ids:
        # qualquer id do índice da empresa, mesmo fora da listagem/filtro de --tipo
        alvo = [por_id[i] for i in ids if i in por_id]
        for i in ids:
            if i not in por_id:
                warn(f"id={i} não encontrado no índice IPE da empresa (últimos 5 anos)")
    else:
        alvo = docs[:baixar]
    for i, r in enumerate(alvo):
        if i:
            time.sleep(1)
        label = r.get("Tipo") or r.get("Categoria") or "doc"
        dest = cache_path("docs", ticker.upper(), f"{r.get('Data_Referencia', '').replace('-', '')}_{slug(label)}_{r['_id']}.pdf")
        if not dest.exists():
            try:
                dest = save_pdf(http_get(r["Link_Download"].strip(), timeout=120), dest)
            except HttpError as e:
                warn(f"falha ao baixar id={r['_id']}: HTTP {e.status}")
                continue
        print(f"baixado: {dest}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, tipos, default in (("fii", FII_TIPOS, "relatorio"), ("cia", CIA_TIPOS, "release")):
        p = sub.add_parser(name)
        p.add_argument("ticker")
        p.add_argument("--tipo", choices=sorted(tipos), default=default)
        p.add_argument("--busca", help="texto adicional para filtrar tipo/assunto")
        p.add_argument("-n", type=int, default=10, help="quantos listar (padrão 10)")
        p.add_argument("--baixar", type=int, default=0, help="baixa os N primeiros da lista")
        p.add_argument("--ids", default="", help="ids para baixar, separados por vírgula (não precisam estar na lista)")
        p.add_argument("--todas-versoes", action="store_true", help="não deduplica (mostra reapresentações, PT/EN etc.)")
    args = ap.parse_args()
    ids = [i.strip() for i in args.ids.split(",") if i.strip()]
    if args.cmd == "fii":
        cmd_fii(args.ticker, args.tipo, args.busca, args.n, args.baixar, ids, args.todas_versoes)
    else:
        cmd_cia(args.ticker, args.tipo, args.busca, args.n, args.baixar, ids, args.todas_versoes)


if __name__ == "__main__":
    sys.exit(main())
