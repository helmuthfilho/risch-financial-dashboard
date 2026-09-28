#!/usr/bin/env python3
"""Cotações, proventos e histórico via brapi.dev, com saída compacta.

Uso:
  cotacao.py PETR4 MXRF11 HGLG11            # cotação atual (1 chamada agrupada)
  cotacao.py PETR4 --dividendos             # + proventos dos últimos 12 meses e DY 12m
  cotacao.py PETR4 --fundamentos            # + P/L, LPA, valor de mercado
  cotacao.py HGLG11 --historico 1y --intervalo 1mo   # fechamentos mensais
  cotacao.py PETR4 --json                   # JSON enxuto em vez de tabela

Token: variável BRAPI_TOKEN no .env da raiz do repo (nunca na linha de
comando). Vai no header Authorization, nunca na URL. Respostas ficam em cache
local (.cache/analise-fii-acoes/brapi/) por --max-idade minutos para poupar a
cota do plano gratuito.

Limites do plano: o script nunca aborta por recurso fora do plano. Ele lê a
mensagem de erro da brapi e se adapta: sem proventos/fundamentos, segue só
com a cotação; range/intervalo não permitido, troca pelo maior permitido;
chamada agrupada recusada, consulta um ticker por vez. O que o plano não
permite fica gravado em .cache/analise-fii-acoes/brapi/plano.json por 7 dias,
então as chamadas seguintes já saem ajustadas (sem gastar cota com erro).
A saída diz o que foi omitido ou ajustado.

BRAPI_PLANO no .env (ex.: BRAPI_PLANO=gratuito) declara o plano de antemão:
com um plano conhecido o script já sai ajustado na primeira chamada, sem
sondar recurso que o plano não tem. Vazio ou desconhecido = modo de
aprendizado descrito acima. Proventos de FII no plano gratuito: use
proventos.py fii (avisos de rendimentos oficiais do FundosNET).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

from _comum import (
    HttpError,
    cache_path,
    die,
    fmt_brl,
    fmt_num,
    fmt_pct,
    http_get,
    json_cache_get,
    json_cache_put,
    load_env,
    print_table,
    to_cents,
    to_scaled_int,
    warn,
)

BASE = "https://brapi.dev/api/quote/"
UNIT = 10**8  # proventos por cota em 1e-8 de real


def fetch(tickers: List[str], params: Dict[str, str], token: Optional[str], max_age_s: float) -> List[dict]:
    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    key = hashlib.sha1(f"{','.join(tickers)}?{query}".encode()).hexdigest()[:16]
    cp = cache_path("brapi", f"{key}.json")
    cached = json_cache_get(cp, max_age_s)
    if cached is not None:
        return cached
    url = BASE + ",".join(tickers) + (f"?{query}" if query else "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    raw = http_get(url, headers=headers, timeout=20)
    # parse_float=str: preço entra como string e vira centavos sem passar por float
    data = json.loads(raw.decode("utf-8"), parse_float=str)
    results = data.get("results") or []
    json_cache_put(cp, results)
    return results


PLANO_TTL = 7 * 24 * 3600
RECURSOS = {"dividends": "proventos/DY", "fundamental": "fundamentos (P/L, LPA)"}
# limites conhecidos por plano (verificados em 27/09/2026); planos pagos não
# listados aqui caem no modo de aprendizado
PLANOS: Dict[str, dict] = {
    "gratuito": {
        "sem": ["dividends"],
        "ranges": ["1d", "5d", "1mo", "3mo"],
        "intervals": ["1d"],
        "agrupado": False,
    },
}


def plano_declarado() -> Optional[str]:
    nome = (os.environ.get("BRAPI_PLANO") or "").strip().lower()
    return nome or None


def load_plano() -> dict:
    plano = json_cache_get(cache_path("brapi", "plano.json"), PLANO_TTL) or {}
    preset = PLANOS.get(plano_declarado() or "")
    if preset:
        plano.update({k: (list(v) if isinstance(v, list) else v) for k, v in preset.items()})
    return plano


def save_plano(plano: dict) -> None:
    json_cache_put(cache_path("brapi", "plano.json"), plano)


def permitidos(msg: str) -> List[str]:
    """"... Ranges permitidos: 1d, 5d, 1mo, 3mo. Faça..." -> ["1d", "5d", "1mo", "3mo"]."""
    m = re.search(r"permitidos:\s*([^.]+)", msg, re.I)
    return [x.strip() for x in m.group(1).split(",") if x.strip()] if m else []


def learn(plano: dict, msg: str, params: Dict[str, str]) -> bool:
    """Registra no `plano` o limite descrito pela mensagem de erro. True se aprendeu algo."""
    low = msg.lower()
    if "dividends" in params and ("dividendo" in low or "jcp" in low):
        plano.setdefault("sem", []).append("dividends")
        return True
    if "fundamental" in params and "fundament" in low:
        plano.setdefault("sem", []).append("fundamental")
        return True
    if "range" in params and "range" in low and permitidos(msg):
        plano["ranges"] = permitidos(msg)
        return True
    if "interval" in params and "intervalo" in low and permitidos(msg):
        plano["intervals"] = permitidos(msg)
        return True
    return False


def adapt(params: Dict[str, str], plano: dict) -> Tuple[Dict[str, str], List[str]]:
    """Remove/ajusta parâmetros que o plano não permite; devolve notas para a saída."""
    out, notas = dict(params), []
    for k in plano.get("sem", []):
        if k in out:
            del out[k]
            notas.append(f"{RECURSOS.get(k, k)} indisponível(is) no plano atual da brapi")
    for k, chave in (("range", "ranges"), ("interval", "intervals")):
        allowed = plano.get(chave)
        if k in out and allowed and out[k] not in allowed:
            notas.append(f"{k} '{out[k]}' fora do plano; usando '{allowed[-1]}' (permitidos: {', '.join(allowed)})")
            out[k] = allowed[-1]
    return out, notas


def fetch_adapting(
    tickers: List[str], params: Dict[str, str], plano: dict, token: Optional[str], max_age_s: float
) -> List[dict]:
    """Uma chamada; se a brapi recusar um recurso do plano, aprende e repete sem ele."""
    for _ in range(4):
        eff, _ = adapt(params, plano)
        try:
            return fetch(tickers, eff, token, max_age_s)
        except HttpError as e:
            if not learn(plano, brapi_message(e.body), eff):
                raise
            save_plano(plano)
    return fetch(tickers, adapt(params, plano)[0], token, max_age_s)


def fetch_all(tickers: List[str], params: Dict[str, str], plano: dict, token: Optional[str], max_age_s: float) -> List[dict]:
    """Chamada agrupada quando o plano permite; senão, uma por ticker."""
    if len(tickers) > 1 and plano.get("agrupado") is not False:
        try:
            return fetch_adapting(tickers, params, plano, token, max_age_s)
        except HttpError as e:
            warn(f"chamada agrupada recusada (HTTP {e.status}); consultando um ticker por vez")
            plano["agrupado"] = False
            save_plano(plano)
    out: List[dict] = []
    for i, t in enumerate(tickers):
        if i:
            time.sleep(0.5)
        try:
            out.extend(fetch_adapting([t], params, plano, token, max_age_s))
        except HttpError as e:
            if len(tickers) == 1:
                raise
            warn(f"{t}: HTTP {e.status} {brapi_message(e.body)}")
    return out


def cotar(tickers: List[str], fundamentos: bool = False, max_age_s: float = 15 * 60) -> Dict[str, dict]:
    """Preço (e valor de mercado, se pedido) em centavos, por ticker — para outros scripts."""
    load_env()
    token = os.environ.get("BRAPI_TOKEN") or None
    params = {"fundamental": "true"} if fundamentos else {}
    out: Dict[str, dict] = {}
    for r in fetch_all([t.upper() for t in tickers], params, load_plano(), token, max_age_s):
        out[str(r.get("symbol"))] = {
            "preco_cents": to_cents(str(r.get("regularMarketPrice"))),
            "valor_mercado_cents": to_cents(str(r.get("marketCap"))) if r.get("marketCap") else None,
            "hora": r.get("regularMarketTime"),
        }
    return out


def amostra(hist: List[dict], limite: int = 24) -> List[dict]:
    """Reduz séries longas (ex.: diário de 3 meses) a ~`limite` linhas, sempre com a última."""
    if len(hist) <= limite:
        return hist
    passo = -(-len(hist) // limite)
    out = hist[::passo]
    return out if out[-1] is hist[-1] else out + [hist[-1]]


def brapi_message(body: bytes) -> str:
    try:
        return json.loads(body.decode("utf-8")).get("message", "")
    except Exception:  # noqa: BLE001
        return ""


def parse_date(s: Optional[str]) -> Optional[dt.date]:
    if not s:
        return None
    return dt.date.fromisoformat(str(s)[:10])


def proventos_12m(r: dict, today: dt.date) -> List[dict]:
    cash = ((r.get("dividendsData") or {}).get("cashDividends")) or []
    start = today - dt.timedelta(days=365)
    out = []
    for d in cash:
        ex = parse_date(d.get("lastDatePrior")) or parse_date(d.get("exDate"))
        if ex is None or ex < start or ex > today:
            continue
        out.append(
            {
                "data_com": ex.isoformat(),
                "pagamento": (parse_date(d.get("paymentDate")) or "").__str__(),
                "tipo": d.get("label", ""),
                "valor_1e8": to_scaled_int(str(d.get("rate")), 8) or 0,
            }
        )
    out.sort(key=lambda d: d["data_com"], reverse=True)
    return out


def fmt_unit(v: int) -> str:
    return fmt_num(v / UNIT, 4)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tickers", nargs="+", help="ex.: PETR4 MXRF11")
    ap.add_argument("--dividendos", action="store_true", help="proventos com data-com nos últimos 12 meses e DY 12m")
    ap.add_argument("--fundamentos", action="store_true", help="P/L, LPA e valor de mercado")
    ap.add_argument("--historico", metavar="RANGE", help="1mo, 3mo, 6mo, 1y, 2y, 5y, max (limitado pelo plano)")
    ap.add_argument("--intervalo", default="1mo", help="1d, 1wk, 1mo (padrão 1mo)")
    ap.add_argument("--max-idade", type=float, default=15, help="minutos de validade do cache (padrão 15)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    load_env()
    token = os.environ.get("BRAPI_TOKEN") or None
    if not token:
        warn("BRAPI_TOKEN vazio no .env; sem token a brapi só responde alguns tickers de teste")

    tickers = [t.upper() for t in args.tickers]
    params: Dict[str, str] = {}
    if args.dividendos:
        params["dividends"] = "true"
    if args.fundamentos:
        params["fundamental"] = "true"
    if args.historico:
        params["range"] = args.historico
        params["interval"] = args.intervalo

    plano = load_plano()
    try:
        results = fetch_all(tickers, params, plano, token, args.max_idade * 60)
    except HttpError as e:
        die(f"brapi HTTP {e.status}: {brapi_message(e.body)}")
    if not results:
        die("brapi não retornou resultados")
    # o que de fato veio, depois das adaptações ao plano
    efetivos, notas = adapt(params, plano)
    args.dividendos = "dividends" in efetivos
    args.fundamentos = "fundamental" in efetivos
    if "range" in efetivos:
        args.historico, args.intervalo = efetivos["range"], efetivos["interval"]

    today = dt.date.today()
    compact = []
    for r in results:
        price = to_cents(str(r.get("regularMarketPrice")))
        item = {
            "ticker": r.get("symbol"),
            "nome": r.get("longName") or r.get("shortName"),
            "preco_cents": price,
            "var_dia_pct": r.get("regularMarketChangePercent"),
            "hora": r.get("regularMarketTime"),
            "min_52s_cents": to_cents(str(r.get("fiftyTwoWeekLow"))),
            "max_52s_cents": to_cents(str(r.get("fiftyTwoWeekHigh"))),
            "volume": r.get("regularMarketVolume"),
        }
        if args.fundamentos:
            item["pl"] = r.get("priceEarnings")
            item["lpa"] = r.get("earningsPerShare")
            item["valor_mercado_cents"] = to_cents(str(r.get("marketCap"))) if r.get("marketCap") else None
        if args.dividendos:
            provs = proventos_12m(r, today)
            total = sum(p["valor_1e8"] for p in provs)
            item["proventos_12m"] = provs
            item["soma_12m_1e8"] = total
            # DY = soma (1e-8 R$) / preço (1e-2 R$)
            item["dy_12m"] = (total / (price * 10**6)) if price else None
        if args.historico:
            hist = r.get("historicalDataPrice") or []
            item["historico"] = [
                {
                    "data": dt.datetime.fromtimestamp(int(h["date"]), tz=dt.timezone.utc).date().isoformat(),
                    "fech_cents": to_cents(str(h.get("close"))),
                    "fech_ajust_cents": to_cents(str(h.get("adjustedClose"))) if h.get("adjustedClose") else None,
                }
                for h in hist
                if h.get("close") is not None
            ]
        compact.append(item)

    if args.json:
        json.dump({"resultados": compact, "notas": notas}, sys.stdout, ensure_ascii=False, separators=(",", ":"))
        print()
        return

    headers = ["Ticker", "Preço R$", "Dia", "Mín 52s", "Máx 52s", "Hora"]
    if args.fundamentos:
        headers += ["P/L", "LPA", "Mkt cap R$ bi"]
    if args.dividendos:
        headers += ["Prov. 12m R$", "DY 12m"]
    rows = []
    for it in compact:
        row = [
            it["ticker"],
            fmt_brl(it["preco_cents"]),
            (fmt_num(float(it["var_dia_pct"]), 2) + "%") if it["var_dia_pct"] is not None else "-",
            fmt_brl(it["min_52s_cents"]),
            fmt_brl(it["max_52s_cents"]),
            str(it["hora"] or "-")[:16],
        ]
        if args.fundamentos:
            row += [
                fmt_num(float(it["pl"]), 1) if it.get("pl") else "-",
                fmt_num(float(it["lpa"]), 2) if it.get("lpa") else "-",
                fmt_num(it["valor_mercado_cents"] / 1e11, 1) if it.get("valor_mercado_cents") else "-",
            ]
        if args.dividendos:
            row += [fmt_unit(it["soma_12m_1e8"]), fmt_pct(it["dy_12m"], 2)]
        rows.append(row)
    print_table(headers, rows)
    print("Fonte: brapi.dev (cotação com atraso ~15 min no plano gratuito).")
    for n in notas:
        print(f"Nota: {n}.")
    if "dividends" in params and not args.dividendos:
        print("Nota: para proventos/DY use proventos.py fii <FII> (avisos de rendimentos oficiais) ou proventos.py cia <TICKER> (DY aproximado pela DFC).")

    if args.dividendos:
        for it in compact:
            provs = it["proventos_12m"]
            if not provs:
                continue
            print(f"\n{it['ticker']} proventos (data-com últimos 12m):")
            print_table(
                ["Data-com", "Pagamento", "Tipo", "R$/cota"],
                [[p["data_com"], p["pagamento"][:10], p["tipo"], fmt_unit(p["valor_1e8"])] for p in provs],
            )

    if args.historico:
        for it in compact:
            hist = it.get("historico") or []
            if not hist:
                continue
            first, last = hist[0]["fech_cents"], hist[-1]["fech_cents"]
            lo = min(h["fech_cents"] for h in hist)
            hi = max(h["fech_cents"] for h in hist)
            print(
                f"\n{it['ticker']} histórico {args.historico}/{args.intervalo}: "
                f"var {fmt_pct((last - first) / first if first else None)} "
                f"(sem proventos), mín {fmt_brl(lo)}, máx {fmt_brl(hi)}"
            )
            linhas = amostra(hist)
            if len(linhas) < len(hist):
                print(f"({len(hist)} pregões; mostrando {len(linhas)} amostrados, incluindo o último)")
            print_table(["Data", "Fech R$", "Ajust R$"], [[h["data"], fmt_brl(h["fech_cents"]), fmt_brl(h["fech_ajust_cents"])] for h in linhas])


if __name__ == "__main__":
    main()
