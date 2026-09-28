#!/usr/bin/env python3
"""Proventos e DY sem depender do plano pago da brapi.

Uso:
  proventos.py fii HGLG11 [--meses 12] [--sem-preco]
      Rendimentos e amortizações por cota a partir dos avisos oficiais
      (FundosNET, "Aviso aos Cotistas - Estruturado": XML de ~1 KB com
      data-base, valor, pagamento, período e isenção de IR). DY 12m e DY do
      último rendimento anualizado sobre o preço atual (brapi).
  proventos.py cia PETR4 [--trimestres 4] [--sem-preco]
      DY aproximado = dividendos + JCP pagos nos últimos 12 meses (DFC da
      CVM, trimestres isolados) / valor de mercado (brapi). Mede caixa pago
      no período, não proventos por data-com; exclui pagamentos a não
      controladores.

Os XMLs dos avisos ficam em cache permanente (.cache/analise-fii-acoes/fnet/
xml/): histórico não muda, então só avisos novos são baixados. FundosNET é
lento às vezes; o script espera ~1 s entre downloads.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple

from _comum import (
    HttpError,
    cache_path,
    die,
    div,
    fmt_brl,
    fmt_mi,
    fmt_num,
    fmt_pct,
    http_get,
    only_digits,
    print_table,
    quarter_label,
    to_scaled_int,
    warn,
)

UNIT = 10**8  # valores por cota em 1e-8 de real (avisos trazem até 8 casas)
FNET = "https://fnet.bmfbovespa.com.br/fnet/publico"


def fmt_unit(v: Optional[int], casas: int = 4) -> str:
    return "-" if v is None else fmt_num(v / UNIT, casas)


# --------------------------------------------------------------------- FII


def parse_aviso(xml: bytes, ticker: str) -> List[dict]:
    """Extrai rendimentos/amortizações de um aviso estruturado do FundosNET.

    Se o aviso cobre mais de um código (classes/subclasses), fica com o do
    ticker pedido; sem código no XML, aceita o provento.
    """
    root = ET.fromstring(xml)
    out = []
    for prov in root.iter("Provento"):
        cod = (prov.findtext("CodNegociacao") or "").strip().upper()
        if cod and cod != ticker.upper():
            continue
        for tag, tipo in (("Rendimento", "rendimento"), ("Amortizacao", "amortização")):
            for el in prov.iter(tag):
                valor = to_scaled_int(el.findtext("ValorProvento") or el.findtext("ValorProventoCota"), 8)
                base = (el.findtext("DataBase") or "").strip()
                if not valor or not base:
                    continue
                out.append(
                    {
                        "tipo": tipo,
                        "data_base": base,
                        "pagamento": (el.findtext("DataPagamento") or "").strip(),
                        "periodo": (el.findtext("PeriodoReferencia") or "").strip().lower(),
                        "isento": (el.findtext("RendimentoIsentoIR") or "").strip(),
                        "valor_1e8": valor,
                    }
                )
    return out


def dedupe_proventos(itens: List[dict]) -> List[dict]:
    """Mesmo provento (tipo + data-base) reapresentado: fica o do aviso entregue por último."""
    best: Dict[tuple, dict] = {}
    for it in itens:
        k = (it["tipo"], it["data_base"])
        if k not in best or it.get("_entrega", "") >= best[k].get("_entrega", ""):
            best[k] = it
    return sorted(best.values(), key=lambda it: it["data_base"], reverse=True)


def baixar_aviso(doc_id: int) -> Tuple[Optional[bytes], bool]:
    """(conteúdo, falhou_rede). falhou_rede=True vale nova tentativa; documento
    que não é XML estruturado volta (None, False) e é só ignorado."""
    dest = cache_path("fnet", "xml", f"{doc_id}.xml")
    if dest.exists():
        return dest.read_bytes(), False
    try:
        data = http_get(f"{FNET}/downloadDocumento?id={doc_id}", timeout=30, retries=3)
    except (OSError, HttpError) as e:
        warn(f"aviso id={doc_id} não baixou ({e})")
        return None, True
    if not data.lstrip().startswith(b"<"):
        warn(f"aviso id={doc_id} não é XML estruturado; ignorado")
        return None, False
    dest.write_bytes(data)
    return data, False


def completude(faltando: List[str], rend: List[dict]) -> Tuple[bool, bool]:
    """Se ainda faltam avisos (datas de referência ISO; "" se desconhecida):
    (dy_12m_confiavel, ultimo_confiavel). O último rendimento só vale se todo
    aviso faltante for comprovadamente anterior a ele (um faltante na mesma
    data ou mais novo pode ser o último ou uma reapresentação dele)."""
    if not faltando:
        return True, True
    ultimo_base = rend[0]["data_base"] if rend else ""
    ultimo_ok = bool(ultimo_base) and all(ref and ref < ultimo_base for ref in faltando)
    return False, ultimo_ok


def cmd_fii(ticker: str, meses: int, sem_preco: bool) -> None:
    from cvm_fii import resolve
    from documentos import FII_TIPOS, entrega_fnet, fnet_search

    g = resolve(ticker)
    cnpj = only_digits(g["CNPJ_Fundo_Classe"])
    inicio = (dt.date.today() - dt.timedelta(days=int(meses * 30.5))).isoformat()
    # ~2 avisos por mês cobre rendimento + amortização/reapresentações
    docs = fnet_search(cnpj, FII_TIPOS["rendimento"], None, meses * 2 + 4, False, True)
    docs = [d for d in docs if "estruturado" in (d.get("categoriaDocumento") or "").lower()]

    def ref_iso(d: dict) -> str:
        ref = entrega_fnet(d.get("dataReferencia", ""))[:10]
        return ref if re.fullmatch(r"\d{4}-\d{2}-\d{2}", ref) else ""

    # só descarta por data quando a referência é uma data completa
    no_periodo = [d for d in docs if not (ref_iso(d) and ref_iso(d) < inicio)]

    itens: List[dict] = []
    pendentes = list(no_periodo)
    baixados = 0
    for rodada in range(2):  # 2ª rodada só para os que falharam por rede (FundosNET oscila)
        if rodada:
            if not pendentes:
                break
            warn(f"tentando de novo {len(pendentes)} aviso(s) que falharam")
            time.sleep(3)
        falharam = []
        for d in pendentes:
            novo = not cache_path("fnet", "xml", f"{d['id']}.xml").exists()
            if novo and baixados:
                time.sleep(1)
            xml, falhou = baixar_aviso(int(d["id"]))
            baixados += int(novo)
            if falhou:
                falharam.append(d)
            if xml is None:
                continue
            for it in parse_aviso(xml, ticker):
                it["_entrega"] = entrega_fnet(d.get("dataEntrega", ""))
                it["_id"] = d["id"]
                itens.append(it)
        pendentes = falharam
    itens = [it for it in dedupe_proventos(itens) if it["data_base"] >= inicio]

    print(f"{g['Nome_Fundo_Classe']} ({ticker.upper()}) — avisos de rendimentos (FundosNET), data-base desde {inicio}:")
    if pendentes:
        lista = ", ".join(f"id={d['id']} (ref {d.get('dataReferencia', '?')})" for d in pendentes)
        print(
            f"INCOMPLETO: {len(pendentes)} aviso(s) não baixaram após 2 tentativas (FundosNET): {lista}. "
            "Soma e DY dos 12 meses não são calculados; rode de novo mais tarde."
        )
    if not itens:
        print("(nenhum aviso estruturado encontrado no período)")
        return
    print_table(
        ["Data-base", "Pagamento", "Período", "Tipo", "R$/cota", "Isento IR"],
        [
            [it["data_base"], it["pagamento"], it["periodo"], it["tipo"], fmt_unit(it["valor_1e8"]), it["isento"]]
            for it in itens
        ],
    )

    rend = [it for it in itens if it["tipo"] == "rendimento"]
    ano = dt.date.today() - dt.timedelta(days=365)
    rend_12m = [it for it in rend if it["data_base"] >= ano.isoformat()]
    soma_12m = sum(it["valor_1e8"] for it in rend_12m)
    amort = sum(it["valor_1e8"] for it in itens if it["tipo"] == "amortização")
    doze_ok, ultimo_ok = completude([ref_iso(d) for d in pendentes], rend)
    ultimo = rend[0]["valor_1e8"] if rend and ultimo_ok else None
    linha = (
        (
            f"Rendimentos 12m: R$ {fmt_unit(soma_12m)} ({len(rend_12m)} pagamentos)"
            if doze_ok
            else f"Rendimentos 12m: n/d (parcial R$ {fmt_unit(soma_12m)} em {len(rend_12m)} avisos; faltam avisos)"
        )
        + (f" | amortizações no período: R$ {fmt_unit(amort)} (devolução de capital, fora do DY)" if amort else "")
        + (f" | último: R$ {fmt_unit(ultimo)} ({rend[0]['periodo'] or rend[0]['data_base']})" if ultimo else "")
    )
    print(linha)
    if rend and not ultimo_ok:
        print("Último rendimento: n/d (um aviso faltante pode ser o último ou uma reapresentação dele).")
    if doze_ok and len(rend_12m) < 12 and meses >= 12:
        print(f"Aviso: só {len(rend_12m)} rendimentos em 12 meses — fundo novo, pagamento não mensal ou avisos faltando no FundosNET.")

    if sem_preco:
        return
    from cotacao import cotar

    try:
        preco = cotar([ticker]).get(ticker.upper(), {}).get("preco_cents")
    except (OSError, HttpError) as e:
        warn(f"cotação indisponível ({e}); DY não calculado")
        return
    if not preco:
        warn("cotação indisponível; DY não calculado")
        return
    # valores em 1e-8 R$, preço em 1e-2 R$; DY 12m só com os avisos completos
    dy12 = soma_12m / (preco * 10**6) if doze_ok else None
    dy_ult = (ultimo * 12) / (preco * 10**6) if ultimo else None
    print(
        f"Preço R$ {fmt_brl(preco)} (brapi) | DY 12m: {fmt_pct(dy12, 2) if dy12 is not None else 'n/d'} | "
        f"DY do último rendimento anualizado (×12): {fmt_pct(dy_ult, 2) if dy_ult is not None else 'n/d'}"
    )
    print("DY calculado (proventos oficiais / preço atual); rendimento de FII isento de IR para PF nas regras vigentes.")


# --------------------------------------------------------------------- CIA

DIV_RX = re.compile(r"dividend|juros sobre (o )?capital pr|\bjcp\b", re.I)
EXCLUI_RX = re.compile(r"n[ãa]o controlador|minorit|recebid", re.I)


def cmd_cia(ticker: str, trimestres: int, sem_preco: bool) -> None:
    from cvm_cia import header, load

    info, d, _, _ = load(ticker, max(trimestres, 4), False)
    header(info)
    # contas escolhidas pelo nome em cada período: o código muda entre ITR e DFP
    serie = d.serie_por_nome("DFC", DIV_RX.pattern, EXCLUI_RX.pattern, "6.03")
    if not any(serie.values()):
        die("nenhuma conta de dividendos/JCP pagos encontrada na DFC (6.03); veja `cvm_cia.py plano TICKER --demonstracao DFC`")
    ends = sorted(serie)
    pagos: List[Optional[int]] = [None if serie[e] is None else -serie[e] for e in ends]  # saída de caixa é negativa
    show = list(range(len(ends)))[-trimestres:]
    print("\nDividendos + JCP pagos a acionistas da companhia (DFC consolidada, R$ mi; contas 6.03 casadas pelo nome):")
    print_table([quarter_label(ends[i]) for i in show], [[fmt_mi(pagos[i]) for i in show]])

    ult4 = pagos[-4:]
    ltm = sum(ult4) if len(ult4) == 4 and all(v is not None for v in ult4) else None
    print(f"Pagos nos últimos 12 meses (até {quarter_label(ends[-1])}): R$ {fmt_mi(ltm)} mi")
    if sem_preco or ltm is None:
        return
    from cotacao import cotar

    # units (ex.: TAEE11) vêm sem valor de mercado na brapi; as classes ON/PN da
    # mesma companhia trazem o valor da companhia inteira
    candidatos = [ticker.upper()] + [t for t in (info.get("TICKERS") or "").split(",") if t and t != ticker.upper()]
    mc, fonte = None, ""
    for t in candidatos:
        try:
            mc = cotar([t], fundamentos=True).get(t, {}).get("valor_mercado_cents")
        except (OSError, HttpError) as e:
            warn(f"{t}: valor de mercado indisponível ({e})")
            continue
        if mc:
            fonte = t
            break
    if not mc:
        warn("valor de mercado indisponível na brapi para os tickers da companhia; DY não calculado")
        return
    via = "" if fonte == ticker.upper() else f", via {fonte}"
    print(
        f"Valor de mercado R$ {fmt_mi(mc)} mi (brapi{via}) | DY aproximado 12m: {fmt_pct(div(ltm, mc), 2)}\n"
        "DY aproximado = caixa pago a acionistas nos últimos 4 trimestres / valor de mercado atual. "
        "Não é DY por data-com: pagamentos atrasados ou antecipados distorcem; JCP entra bruto (antes do IR de 15%). "
        "Confirme se o valor de mercado da brapi é o da companhia inteira (todas as classes)."
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("fii")
    p.add_argument("ticker")
    p.add_argument("--meses", type=int, default=12)
    p.add_argument("--sem-preco", action="store_true", help="não consulta a brapi (só os proventos)")
    p = sub.add_parser("cia")
    p.add_argument("ticker")
    p.add_argument("--trimestres", type=int, default=4)
    p.add_argument("--sem-preco", action="store_true", help="não consulta a brapi (só os valores pagos)")
    args = ap.parse_args()
    if args.cmd == "fii":
        cmd_fii(args.ticker, args.meses, args.sem_preco)
    else:
        cmd_cia(args.ticker, args.trimestres, args.sem_preco)


if __name__ == "__main__":
    sys.exit(main())
