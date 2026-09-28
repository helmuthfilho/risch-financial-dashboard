#!/usr/bin/env python3
"""Dados estruturados de FIIs a partir do CVM Dados Abertos (informes oficiais).

Uso:
  cvm_fii.py mensal HGLG11 [--meses 24]     # série mensal: PL, VP/cota, cotistas, DY, caixa, passivos
  cvm_fii.py trimestral HGLG11 [--trimestres 8] [--top 10]
                                            # resultado caixa x distribuição, imóveis/vacância,
                                            # inquilinos, vencimento/indexador de contratos, carteira
  cvm_fii.py pares HGLG11 [--top 15] [--segmento Logística]
                                            # fundos do mesmo segmento por PL (último informe mensal);
                                            # --segmento corrige segmento autodeclarado errado/genérico
  cvm_fii.py resolver HGLG11                # só mostra CNPJ/nome/segmento

Aceita ticker (ex.: HGLG11) ou CNPJ. O mapeamento ticker -> fundo usa o
código ISIN do informe (BR + 4 letras do ticker + CTF...). Os ZIPs ficam em
.cache/analise-fii-acoes/cvm/ e são reaproveitados entre chamadas.

Fonte: https://dados.cvm.gov.br/dados/FII/DOC/ (defasagem de semanas após o
fim de cada período). Valores em R$ milhões salvo indicação.
"""

from __future__ import annotations

import argparse
import sys
import time
import unicodedata
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from _comum import (
    cache_path,
    cvm_max_age,
    die,
    div,
    download_cached,
    fmt_brl,
    fmt_mi,
    fmt_num,
    fmt_pct,
    iter_zip_csv,
    latest_version,
    only_digits,
    print_table,
    quarter_label,
    to_cents,
    to_ratio,
    warn,
)

BASE = "https://dados.cvm.gov.br/dados/FII/DOC"
KEY = ("CNPJ_Fundo_Classe", "Data_Referencia")


def zip_for(kind: str, year: int):
    """kind: 'mensal' | 'trimestral'."""
    folder = "INF_MENSAL" if kind == "mensal" else "INF_TRIMESTRAL"
    name = f"inf_{kind}_fii_{year}.zip"
    return download_cached(f"{BASE}/{folder}/DADOS/{name}", cache_path("cvm", "fii", name), cvm_max_age(year))


def recent_zips(kind: str, years: int) -> List[Tuple[int, object]]:
    this_year = time.localtime().tm_year
    out = []
    for y in range(this_year - years + 1, this_year + 1):
        z = zip_for(kind, y)
        if z is not None:
            out.append((y, z))
    if not out:
        die(f"nenhum informe {kind} de FII encontrado na CVM")
    return out


def read(kind: str, zips, table: str, cnpj: Optional[str] = None) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for y, z in zips:
        pre = (lambda line: cnpj in line) if cnpj else None
        rows.extend(iter_zip_csv(z, f"inf_{kind}_fii_{table}_{y}.csv", pre))
    if cnpj:
        rows = [r for r in rows if r["CNPJ_Fundo_Classe"] == cnpj]
    return latest_version(rows, KEY, "Versao") if rows else rows


def fmt_cnpj(digits: str) -> str:
    d = digits.zfill(14)
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"


def ticker_from_isin(isin: str) -> str:
    return isin[2:6] + "11" if isin and isin.startswith("BR") and len(isin) >= 6 else ""


def resolve(ident: str) -> Dict[str, str]:
    """Ticker ou CNPJ -> linha mais recente do cadastro geral do informe mensal."""
    zips = recent_zips("mensal", 2)
    digits = only_digits(ident)
    if len(digits) == 14:
        cnpj = fmt_cnpj(digits)
        rows = read("mensal", zips, "geral", cnpj)
    else:
        code = ident.upper()[:4]
        rows = [
            r
            for y, z in zips
            for r in iter_zip_csv(z, f"inf_mensal_fii_geral_{y}.csv", lambda line: f"BR{code}" in line)
            if r.get("Codigo_ISIN", "")[2:6] == code
        ]
    if not rows:
        die(f"FII '{ident}' não encontrado nos informes mensais da CVM (é uma unit/ação? tente cvm_cia.py)")
    rows.sort(key=lambda r: r["Data_Referencia"])
    by_cnpj: Dict[str, Dict[str, str]] = {}
    for r in rows:
        by_cnpj[r["CNPJ_Fundo_Classe"]] = r
    if len(by_cnpj) > 1:
        others = ", ".join(f"{c} ({r['Nome_Fundo_Classe']})" for c, r in by_cnpj.items())
        warn(f"mais de um fundo/classe para '{ident}': {others}; usando o de informe mais recente")
    return rows[-1]


def header(g: Dict[str, str]) -> None:
    print(
        f"{g['Nome_Fundo_Classe']} | CNPJ {g['CNPJ_Fundo_Classe']} | ISIN {g.get('Codigo_ISIN', '')} | "
        f"segmento: {g.get('Segmento_Atuacao') or '-'} | mandato: {g.get('Mandato') or '-'} | "
        f"gestão: {g.get('Tipo_Gestao') or '-'} | adm: {g.get('Nome_Administrador') or '-'} | "
        f"público: {g.get('Publico_Alvo') or '-'}"
    )


def c(r: Optional[Dict[str, str]], *fields: str) -> Optional[int]:
    """Soma campos monetários (centavos); None se todos vazios."""
    if r is None:
        return None
    vals = [to_cents(r.get(f)) for f in fields]
    vals = [v for v in vals if v is not None]
    return sum(vals) if vals else None


# ------------------------------------------------------------------ mensal


def cmd_mensal(ident: str, meses: int) -> None:
    g = resolve(ident)
    cnpj = g["CNPJ_Fundo_Classe"]
    header(g)
    zips = recent_zips("mensal", meses // 12 + 2)
    comp = {r["Data_Referencia"]: r for r in read("mensal", zips, "complemento", cnpj)}
    ap = {r["Data_Referencia"]: r for r in read("mensal", zips, "ativo_passivo", cnpj)}
    dates = sorted(comp)[-meses:]
    if not dates:
        die("sem informes mensais para esse fundo")

    rows = []
    prev_cotas = None
    emissoes = []
    for d in dates:
        r, a = comp[d], ap.get(d)
        cotas = to_ratio(r.get("Cotas_Emitidas"))
        if prev_cotas and cotas and cotas > prev_cotas * 1.005:
            emissoes.append(f"{d[:7]} (+{fmt_pct(cotas / prev_cotas - 1)} cotas)")
        prev_cotas = cotas or prev_cotas
        rows.append(
            [
                d[:7],
                fmt_mi(to_cents(r.get("Patrimonio_Liquido"))),
                fmt_brl(to_cents(r.get("Valor_Patrimonial_Cotas"))),
                fmt_num(to_ratio(r.get("Total_Numero_Cotistas")), 0),
                fmt_pct(to_ratio(r.get("Percentual_Dividend_Yield_Mes")), 2),
                fmt_pct(to_ratio(r.get("Percentual_Rentabilidade_Patrimonial_Mes")), 2),
                fmt_pct(to_ratio(r.get("Percentual_Despesas_Taxa_Administracao")), 3),
                fmt_mi(c(a, "Disponibilidades", "Titulos_Publicos", "Titulos_Privados", "Fundos_Renda_Fixa")),
                fmt_mi(c(a, "Direitos_Bens_Imoveis")),
                fmt_mi(c(a, "CRI", "CRI_CRA", "LCI", "LCI_LCA")),
                fmt_mi(c(a, "FII")),
                fmt_mi(c(a, "Obrigacoes_Aquisicao_Imoveis", "Obrigacoes_Securitizacao_Recebiveis")),
                fmt_mi(c(a, "Total_Passivo")),
            ]
        )
    print_table(
        [
            "Mês", "PL", "VP/cota R$", "Cotistas", "DY mês*", "Rent.patr.", "Tx adm/PL",
            "Caixa+RF", "Imóveis", "CRI/LCI", "Cotas FII", "Obrig.aquis+secur.", "Passivo",
        ],
        rows,
    )

    first, last = comp[dates[0]], comp[dates[-1]]
    a_last = ap.get(dates[-1])
    pl = to_cents(last.get("Patrimonio_Liquido"))
    vp0, vp1 = to_cents(first.get("Valor_Patrimonial_Cotas")), to_cents(last.get("Valor_Patrimonial_Cotas"))
    dy12 = [to_ratio(comp[d].get("Percentual_Dividend_Yield_Mes")) for d in dates[-12:]]
    liquidez = c(a_last, "Disponibilidades", "Titulos_Publicos", "Titulos_Privados", "Fundos_Renda_Fixa")
    ativo = to_cents(last.get("Valor_Ativo"))
    obrig = c(a_last, "Obrigacoes_Aquisicao_Imoveis", "Obrigacoes_Securitizacao_Recebiveis")
    print(
        f"Resumo {dates[0][:7]}→{dates[-1][:7]}: VP/cota {fmt_pct(div(vp1 - vp0, vp0) if vp0 and vp1 else None)}; "
        f"DY informado soma últimos {len(dy12)}m {fmt_pct(sum(x for x in dy12 if x) if dy12 else None, 2)}; "
        f"caixa+RF/ativo {fmt_pct(div(liquidez, ativo))}; obrigações(aquis.+secur.)/PL {fmt_pct(div(obrig, pl))}; "
        f"emissões detectadas: {', '.join(emissoes) or 'nenhuma'}."
    )
    print("*DY mês e rentabilidade são os percentuais informados pelo administrador à CVM (base pode diferir do preço de mercado).")


# -------------------------------------------------------------- trimestral


VENC_FAIXAS = [
    ("Ate_3Meses", "≤3m"), ("3a6Meses", "3-6m"), ("6a9Meses", "6-9m"), ("9a12Meses", "9-12m"),
    ("12a15Meses", "12-15m"), ("15a18Meses", "15-18m"), ("18a21Meses", "18-21m"), ("21a24Meses", "21-24m"),
    ("24a27Meses", "24-27m"), ("27a30Meses", "27-30m"), ("30a33Meses", "30-33m"), ("33a36Meses", "33-36m"),
    ("Acima_36Meses", ">36m"), ("Indeterminado", "indet."),
]


def cmd_trimestral(ident: str, trimestres: int, top: int) -> None:
    g = resolve(ident)
    cnpj = g["CNPJ_Fundo_Classe"]
    header(g)
    zips = recent_zips("trimestral", trimestres // 4 + 2)

    res = {r["Data_Referencia"]: r for r in read("trimestral", zips, "resultado_contabil_financeiro", cnpj)}
    dates = sorted(res)[-trimestres:]
    if not dates:
        die("sem informes trimestrais para esse fundo")
    print("\nResultado (regime caixa/financeiro, R$ mi). Acumulado e declarados = acumulados no semestre.")
    rows = []
    for d in dates:
        r = res[d]
        rows.append(
            [
                quarter_label(d),
                fmt_mi(c(r, "Receita_Aluguel_Investimento_Financeiro")),
                fmt_mi(c(r, "Resultado_Liquido_Renda_Investimento_Financeiro")),
                fmt_mi(c(r, "Resultado_Liquido_TVM_Financeiro")),
                fmt_mi(c(r, "Resultado_Liquido_Recurso_Liquidez_Financeiro")),
                fmt_mi(c(r, "Taxa_Administracao_Financeiro", "Taxa_Desempenho_Financeiro")),
                fmt_mi(c(r, "Resultado_Trimestral_Liquido_Financeiro")),
                fmt_mi(c(r, "Resultado_Trimestral_Liquido_Contabil")),
                fmt_mi(c(r, "Resultado_Financeiro_Liquido_Acumulado")),
                fmt_mi(c(r, "Rendimentos_Declarados")),
                fmt_pct(to_ratio(r.get("Percentual_Resultado_Financeiro_Liquido_Declarado"))),
                fmt_mi(c(r, "Parcela_Rendimento_Retido")),
            ]
        )
    print_table(
        [
            "Tri", "Aluguel", "Res.imóveis", "Res.TVM(CRI/FII)", "Res.liquidez", "Tx adm+perf",
            "Res.tri caixa", "Res.tri contábil", "Acum.caixa", "Declarados", "Decl/acum", "Retido",
        ],
        rows,
    )

    last = dates[-1]
    print(f"\nDetalhe do último trimestre ({quarter_label(last)}):")

    imoveis = [r for r in read("trimestral", zips, "imovel", cnpj) if r["Data_Referencia"] == last]
    if imoveis:
        area_tot = sum(to_ratio(r.get("Area")) or 0 for r in imoveis)
        vac_pond = sum((to_ratio(r.get("Area")) or 0) * (to_ratio(r.get("Percentual_Vacancia")) or 0) for r in imoveis)
        rec_vagos = sum(
            (to_ratio(r.get("Percentual_Receitas_FII")) or 0) for r in imoveis if (to_ratio(r.get("Percentual_Vacancia")) or 0) > 0
        )
        inad = [r for r in imoveis if (to_ratio(r.get("Percentual_Inadimplencia")) or 0) > 0]
        print(
            f"Imóveis: {len(imoveis)} | área {fmt_num(area_tot, 0)} m² | vacância física ponderada por área "
            f"{fmt_pct(div(vac_pond, area_tot))} | imóveis com vacância>0 respondem por {fmt_pct(rec_vagos)} da receita | "
            f"com inadimplência>0: {len(inad)}"
        )
        imoveis.sort(key=lambda r: to_ratio(r.get("Percentual_Receitas_FII")) or 0, reverse=True)
        print_table(
            ["Imóvel", "Classe", "Área m²", "Vacância", "Inadimpl.", "% receita FII"],
            [
                [
                    (r.get("Nome_Imovel") or "")[:40],
                    (r.get("Classe") or "")[:22],
                    fmt_num(to_ratio(r.get("Area")), 0),
                    fmt_pct(to_ratio(r.get("Percentual_Vacancia"))),
                    fmt_pct(to_ratio(r.get("Percentual_Inadimplencia"))),
                    fmt_pct(to_ratio(r.get("Percentual_Receitas_FII"))),
                ]
                for r in imoveis[:top]
            ],
        )
        if len(imoveis) > top:
            print(f"(+{len(imoveis) - top} imóveis; use --top para ver mais)")

    inq = [r for r in read("trimestral", zips, "imovel_renda_acabado_inquilino", cnpj) if r["Data_Referencia"] == last]
    if inq:
        setores: Dict[str, float] = defaultdict(float)
        for r in inq:
            setores[r.get("Setor_Atuacao") or "?"] += to_ratio(r.get("Percentual_Receitas_FII")) or 0
        maior = max(inq, key=lambda r: to_ratio(r.get("Percentual_Receitas_FII")) or 0)
        print(
            f"\nInquilinos: {len(inq)} linhas | maior inquilino individual (imóvel {maior.get('Nome_Imovel')}): "
            f"{fmt_pct(to_ratio(maior.get('Percentual_Receitas_FII')))} da receita | por setor: "
            + "; ".join(f"{s} {fmt_pct(v)}" for s, v in sorted(setores.items(), key=lambda x: -x[1])[:8])
        )

    comp = [r for r in read("trimestral", zips, "complemento", cnpj) if r["Data_Referencia"] == last]
    if comp:
        r = comp[0]
        venc = [
            f"{lbl} {fmt_pct(to_ratio(r.get('Percentual_Vencimento_Receita_FII_Faixa_' + k)))}"
            for k, lbl in VENC_FAIXAS
            if (to_ratio(r.get("Percentual_Vencimento_Receita_FII_Faixa_" + k)) or 0) > 0
        ]
        idx = [
            f"{n} {fmt_pct(to_ratio(r.get('Percentual_Indexador_Receita_FII_' + n)))}"
            for n in ("IPCA", "IGPM", "INPC", "INCC")
            if (to_ratio(r.get("Percentual_Indexador_Receita_FII_" + n)) or 0) > 0
        ]
        print(f"\nVencimento dos contratos (% receita): {'; '.join(venc) or '-'}")
        print(f"Indexadores (% receita): {'; '.join(idx) or '-'}")
        caract = (r.get("Caracteristicas_Contratuais") or "").strip()
        if caract and caract != "-":
            print(f"Características contratuais (texto do administrador): {caract[:400]}")

    ativos = [r for r in read("trimestral", zips, "ativo", cnpj) if r["Data_Referencia"] == last]
    if ativos:
        por_tipo: Dict[str, int] = defaultdict(int)
        for r in ativos:
            por_tipo[r.get("Tipo") or "?"] += to_cents(r.get("Valor")) or 0
        total = sum(por_tipo.values())
        print(
            f"\nCarteira de títulos/cotas: {len(ativos)} ativos, total R$ {fmt_mi(total)} mi | "
            + "; ".join(f"{t} {fmt_pct(div(v, total))}" for t, v in sorted(por_tipo.items(), key=lambda x: -x[1]))
        )
        ativos.sort(key=lambda r: to_cents(r.get("Valor")) or 0, reverse=True)
        print_table(
            ["Tipo", "Emissor", "Ativo/série", "Venc.", "R$ mi", "% carteira"],
            [
                [
                    (r.get("Tipo") or "")[:20],
                    (r.get("Emissor") or "")[:45],
                    " ".join(x for x in (r.get("Nome_Ativo"), r.get("Emissao"), r.get("Serie")) if x)[:30] or "-",
                    r.get("Data_Vencimento") or "-",
                    fmt_mi(to_cents(r.get("Valor"))),
                    fmt_pct(div(to_cents(r.get("Valor")), total)),
                ]
                for r in ativos[:top]
            ],
        )
    print("\nFonte: CVM, informe trimestral de FII. Vacância aqui é física por imóvel (financeira não é informada).")


# ------------------------------------------------------------------- pares


def norm_txt(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(ch for ch in s if not unicodedata.combining(ch)).strip()


def cmd_pares(ident: str, top: int, segmento: Optional[str]) -> None:
    g = resolve(ident)
    cnpj = g["CNPJ_Fundo_Classe"]
    header(g)
    zips = recent_zips("mensal", 1)
    geral = read("mensal", zips, "geral")
    last_date = max(r["Data_Referencia"] for r in geral if r["CNPJ_Fundo_Classe"] == cnpj)
    no_mes = [r for r in geral if r["Data_Referencia"] == last_date and r.get("Mercado_Negociacao_Bolsa") == "S"]
    segmentos = sorted({r.get("Segmento_Atuacao") or "" for r in no_mes} - {""})

    # --segmento sobrescreve o segmento autodeclarado (às vezes errado ou genérico,
    # ex.: fundo logístico declarado como "Multicategoria"); casa sem acento/maiúscula
    if segmento:
        alvo = [x for x in segmentos if norm_txt(x) == norm_txt(segmento)] or [
            x for x in segmentos if norm_txt(segmento) in norm_txt(x)
        ]
        if not alvo:
            die(f"segmento '{segmento}' não encontrado. Segmentos em {last_date[:7]}: {'; '.join(segmentos)}")
        seg = alvo[0]
    else:
        seg = g.get("Segmento_Atuacao") or ""
        if norm_txt(seg) in ("multicategoria", "hibrido", "outros", ""):
            warn(f"segmento autodeclarado '{seg}' é genérico; considere --segmento (disponíveis: {'; '.join(segmentos)})")

    peers = {r["CNPJ_Fundo_Classe"]: r for r in no_mes if r.get("Segmento_Atuacao") == seg}
    fora_do_segmento = cnpj not in peers
    peers[cnpj] = next(r for r in geral if r["CNPJ_Fundo_Classe"] == cnpj and r["Data_Referencia"] == last_date)
    comp = {
        r["CNPJ_Fundo_Classe"]: r
        for r in read("mensal", zips, "complemento")
        if r["Data_Referencia"] == last_date and r["CNPJ_Fundo_Classe"] in peers
    }
    ranked = sorted(
        (r for c, r in comp.items() if c != cnpj), key=lambda r: to_cents(r.get("Patrimonio_Liquido")) or 0, reverse=True
    )[:top]
    if cnpj in comp:
        ranked = [comp[cnpj]] + ranked  # o fundo analisado sempre na 1ª linha, como referência
    origem = "informado via --segmento" if segmento else "autodeclarado do fundo"
    print(f"\nPares no segmento '{seg}' ({origem}), negociados em bolsa, informe de {last_date[:7]} (top {top} por PL):")
    if fora_do_segmento:
        print(f"(o fundo analisado declara '{g.get('Segmento_Atuacao') or '-'}'; aparece na 1ª linha só como referência)")
    print_table(
        ["Ticker*", "Fundo", "PL R$ mi", "VP/cota R$", "Cotistas", "DY mês", "Tx adm/PL", "Gestão"],
        [
            [
                ("▶ " if r["CNPJ_Fundo_Classe"] == cnpj else "") + ticker_from_isin(peers[r["CNPJ_Fundo_Classe"]].get("Codigo_ISIN", "")),
                peers[r["CNPJ_Fundo_Classe"]]["Nome_Fundo_Classe"][:40],
                fmt_mi(to_cents(r.get("Patrimonio_Liquido"))),
                fmt_brl(to_cents(r.get("Valor_Patrimonial_Cotas"))),
                fmt_num(to_ratio(r.get("Total_Numero_Cotistas")), 0),
                fmt_pct(to_ratio(r.get("Percentual_Dividend_Yield_Mes")), 2),
                fmt_pct(to_ratio(r.get("Percentual_Despesas_Taxa_Administracao")), 3),
                peers[r["CNPJ_Fundo_Classe"]].get("Tipo_Gestao") or "-",
            ]
            for r in ranked
        ],
    )
    print("*Ticker inferido do ISIN (4 letras + 11); confirme antes de cotar. P/VP: use cotacao.py e divida pelo VP/cota.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("mensal")
    p.add_argument("fundo")
    p.add_argument("--meses", type=int, default=24)
    p = sub.add_parser("trimestral")
    p.add_argument("fundo")
    p.add_argument("--trimestres", type=int, default=8)
    p.add_argument("--top", type=int, default=10)
    p = sub.add_parser("pares")
    p.add_argument("fundo")
    p.add_argument("--top", type=int, default=15)
    p.add_argument("--segmento", help="sobrescreve o segmento autodeclarado (ex.: Logística, Lajes Corporativas, Shoppings)")
    p = sub.add_parser("resolver")
    p.add_argument("fundo")
    args = ap.parse_args()

    if args.cmd == "mensal":
        cmd_mensal(args.fundo, args.meses)
    elif args.cmd == "trimestral":
        cmd_trimestral(args.fundo, args.trimestres, args.top)
    elif args.cmd == "pares":
        cmd_pares(args.fundo, args.top, args.segmento)
    else:
        header(resolve(args.fundo))


if __name__ == "__main__":
    sys.exit(main())
