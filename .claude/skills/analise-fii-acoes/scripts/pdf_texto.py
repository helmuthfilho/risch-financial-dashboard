#!/usr/bin/env python3
"""Extrai texto de relatórios em PDF em pedaços pequenos, para gastar poucos tokens.

Estratégia recomendada: primeiro --mapa (1 linha por página), depois só as
páginas que importam com --paginas, ou --buscar por termos do checklist.

Uso (rodar com o Python do venv da skill, que tem pdfplumber):
  pdf_texto.py relatorio.pdf --mapa [--perfil fii|cia]
      Por página: nº de caracteres, título provável, nº de tabelas e quais
      termos do checklist aparecem. Detecta PDF escaneado (sem texto).
  pdf_texto.py relatorio.pdf --paginas 3-5,9 [--tabelas]
      Texto limpo dessas páginas (cabeçalho/rodapé repetidos removidos).
      --tabelas: tabelas como linhas "a | b | c" em vez do texto corrido.
  pdf_texto.py relatorio.pdf --buscar "vacância,inadimpl,carência" [--contexto 1]
      Só as linhas que casam (sem acento/maiúscula), com página e contexto.
  --paginas também restringe --mapa e --buscar (ex.: --buscar "perdas"
  --paginas 1-28 para ignorar a tradução em inglês de um release bilíngue).

Vários PDFs de uma vez (ex.: os releases dos últimos 3 trimestres, do mais
recente para o mais antigo) aplicam a mesma operação a cada arquivo, com um
cabeçalho "=== arquivo" por PDF; com --buscar, termina com uma tabela de
ocorrências termo x arquivo (o que apareceu ou sumiu entre relatórios):
  pdf_texto.py rel_2T26.pdf rel_1T26.pdf rel_4T25.pdf --buscar "guidance,risco sacado,não recorrente"

  pdf_texto.py relatorio.pdf --imagem 9 [--recorte 0.45,0,1,1] [--resolucao 110]
      Salva a(s) página(s) como PNG em .cache/analise-fii-acoes/imagens/ e
      imprime o caminho — depois leia o PNG com a ferramenta Read. Serve para
      gráficos (ex.: evolução da reserva) e PDFs escaneados, sem depender do
      poppler. Recorte só a área do gráfico para gastar menos tokens.

--max-chars (padrão 25000, somado entre os arquivos) corta a saída e avisa, para não despejar um PDF
inteiro na conversa por engano.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence

try:
    import pdfplumber
except ImportError:  # pragma: no cover - mensagem de setup
    sys.exit(
        "erro: pdfplumber não instalado. Rode:\n"
        "  python3 -m venv .claude/skills/analise-fii-acoes/.venv && "
        ".claude/skills/analise-fii-acoes/.venv/bin/pip install -r .claude/skills/analise-fii-acoes/requirements.txt\n"
        "e execute este script com .claude/skills/analise-fii-acoes/.venv/bin/python"
    )

logging.getLogger("pdfminer").setLevel(logging.ERROR)  # avisos de cor/fonte irrelevantes

PERFIS: Dict[str, List[str]] = {
    "fii": [
        "resultado", "distribui", "rendimento", "reserva", "vacancia", "inadimpl", "carencia", "desconto",
        "revisional", "renegoci", "vencimento", "wault", "wale", "prazo medio", "ipca", "igp-m", "cdi", "ltv",
        "subordina", "garantia", "high yield", "high grade", "cri", "alavanc", "obrigac", "emissao",
        "p/vp", "cap rate", "avaliac", "reavalia", "aquisic", "venda", "ganho de capital", "guidance",
        "taxa de administrac", "performance", "partes relacionadas", "conflito",
    ],
    "cia": [
        "receita liquida", "ebitda", "ajustad", "nao recorrente", "margem", "lucro liquido", "divida liquida", "alavancagem", "covenant", "capex", "fluxo de caixa", "capital de giro",
        "risco sacado", "forfait", "fornecedores", "impairment", "contingenc", "guidance", "jcp",
        "dividend", "recompra", "cambio", "hedge", "same store", "sss", "npl", "basileia", "inadimpl",
        "sinistralidade", "vso", "arr", "churn", "partes relacionadas", "ressalva", "enfase",
    ],
}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def term_regex(term: str) -> "re.Pattern[str]":
    """Casa no início de palavra (radicais como "inadimpl"); siglas curtas exigem palavra inteira."""
    t = re.escape(norm(term))
    return re.compile(r"\b" + t + (r"\b" if len(term) <= 4 else ""))


def parse_pages(spec: str, total: int) -> List[int]:
    pages: List[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            pages.extend(range(int(a), min(int(b), total) + 1))
        else:
            pages.append(int(part))
    return [p for p in pages if 1 <= p <= total]


def clean_lines(text: str) -> List[str]:
    out = []
    for ln in (text or "").splitlines():
        ln = re.sub(r"[ \t]+", " ", ln).strip()
        if ln:
            out.append(ln)
    return out


def repeated_lines(pages_lines: Sequence[List[str]]) -> set:
    """Linhas (ignorando números) que aparecem em >50% das páginas = cabeçalho/rodapé."""
    if len(pages_lines) < 4:
        return set()
    cnt: Counter = Counter()
    for lines in pages_lines:
        cnt.update({re.sub(r"\d+", "#", ln) for ln in lines[:3] + lines[-3:]})
    limit = len(pages_lines) / 2
    return {k for k, v in cnt.items() if v > limit}


class Saida:
    def __init__(self, max_chars: int):
        self.max = max_chars
        self.n = 0
        self.cortado = False

    def write(self, s: str) -> bool:
        if self.cortado:
            return False
        if self.n + len(s) > self.max:
            sys.stdout.write(s[: max(0, self.max - self.n)])
            sys.stdout.write(
                f"\n[... saída cortada em {self.max} caracteres; use --paginas menores, --buscar ou --max-chars]\n"
            )
            self.cortado = True
            return False
        sys.stdout.write(s)
        self.n += len(s)
        return True


def renderizar(pdf, arquivo: str, paginas: List[int], args, out: "Saida") -> bool:
    """Salva as páginas como PNG (para ler gráficos/escaneados como imagem) e imprime os caminhos."""
    from _comum import cache_path

    recorte = None
    if args.recorte:
        try:
            recorte = [float(x) for x in args.recorte.split(",")]
            assert len(recorte) == 4 and all(0 <= x <= 1 for x in recorte)
        except (ValueError, AssertionError):
            sys.exit("erro: --recorte deve ser x0,y0,x1,y1 em frações da página (0 a 1), ex.: 0.45,0,1,1")
    stem = Path(arquivo).stem
    for p in paginas:
        page = pdf.pages[p - 1]
        if recorte:
            x0, y0, x1, y1 = recorte
            page = page.crop((page.width * x0, page.height * y0, page.width * x1, page.height * y1))
        sufixo = "_recorte" if recorte else ""
        dest = cache_path("imagens", f"{stem}_p{p}{sufixo}.png")
        page.to_image(resolution=args.resolucao).save(str(dest))
        if not out.write(f"imagem: {dest}\n"):
            return False
    return True


def processar(arquivo: str, args, out: Saida, contagem: Dict[str, Dict[str, int]]) -> bool:
    """Processa um PDF; devolve False se a saída estourou --max-chars."""
    with pdfplumber.open(arquivo) as pdf:
        total = len(pdf.pages)
        if args.imagem:
            return renderizar(pdf, arquivo, parse_pages(args.imagem, total), args, out)
        # --paginas restringe qualquer modo (texto, --mapa, --buscar); sem ele, mapa e busca veem o PDF todo
        idx = parse_pages(args.paginas, total) if args.paginas else list(range(1, total + 1))
        if not idx:
            out.write(f"=== {arquivo}: {total} páginas | nenhuma página de --paginas existe neste arquivo\n")
            return True
        texts: Dict[int, List[str]] = {p: clean_lines(pdf.pages[p - 1].extract_text()) for p in idx}

        # cabeçalho/rodapé calculado numa amostra de páginas (todas, se já lidas)
        sample = texts if len(idx) == total else {
            p: clean_lines(pdf.pages[p - 1].extract_text()) for p in range(1, total + 1, max(1, total // 12))
        }
        rep = repeated_lines(list(sample.values()))

        def body(p: int) -> List[str]:
            return [ln for ln in texts[p] if re.sub(r"\d+", "#", ln) not in rep]

        vazias = [p for p in idx if sum(len(ln) for ln in texts[p]) < 30]
        meta = f"=== {arquivo}: {total} páginas"
        if len(vazias) > len(idx) / 2:
            meta += (
                f" | AVISO: {len(vazias)} de {len(idx)} páginas sem texto extraível (PDF escaneado/imagem);"
                " gere imagens com --imagem e leia os PNGs (ferramenta Read)"
            )
        out.write(meta + "\n")

        if args.mapa:
            termos = [(t, term_regex(t)) for t in PERFIS.get(args.perfil or "", [])]
            for p in idx:
                lines = body(p)
                chars = sum(len(ln) for ln in lines)
                titulo = next((ln for ln in lines if len(ln) > 3 and not re.fullmatch(r"[\d\W]+", ln)), "")[:70]
                ntab = len(pdf.pages[p - 1].find_tables()) if chars else 0
                low = norm(" ".join(lines))
                hits = [t for t, rx in termos if rx.search(low)]
                linha = f"p{p} {chars}c" + (f" {ntab}tab" if ntab else "") + f" | {titulo}"
                if hits:
                    linha += " | " + ",".join(hits)
                if not out.write(linha + "\n"):
                    return False

        elif args.buscar:
            nomes = [t.strip() for t in args.buscar.split(",") if t.strip()]
            termos = [term_regex(t) for t in nomes]
            achados = 0
            por_termo = contagem.setdefault(arquivo, {t: 0 for t in nomes})
            for p in idx:
                lines = body(p)
                for nome, rx in zip(nomes, termos):
                    por_termo[nome] += sum(1 for ln in lines if rx.search(norm(ln)))
                marcadas = sorted(
                    {
                        j
                        for i, ln in enumerate(lines)
                        if any(rx.search(norm(ln)) for rx in termos)
                        for j in range(max(0, i - args.contexto), min(len(lines), i + args.contexto + 1))
                    }
                )
                if not marcadas:
                    continue
                achados += 1
                bloco = f"--- p{p}\n" + "\n".join(lines[j] for j in marcadas) + "\n"
                if not out.write(bloco):
                    return False
            if not achados:
                out.write("(nenhuma ocorrência)\n")

        else:
            for p in idx:
                if args.tabelas:
                    tabelas = pdf.pages[p - 1].extract_tables()
                    if not tabelas:
                        bloco = f"--- p{p} (sem tabelas detectadas; texto)\n" + "\n".join(body(p)) + "\n"
                    else:
                        partes = []
                        for t_i, tab in enumerate(tabelas, 1):
                            rows = [
                                " | ".join(re.sub(r"\s+", " ", c or "").strip() for c in row)
                                for row in tab
                                if any((c or "").strip() for c in row)
                            ]
                            partes.append(f"[tabela {t_i}]\n" + "\n".join(rows))
                        bloco = f"--- p{p}\n" + "\n".join(partes) + "\n"
                else:
                    bloco = f"--- p{p}\n" + "\n".join(body(p)) + "\n"
                if not out.write(bloco):
                    return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivos", nargs="+", help="um ou mais PDFs (vários = mesma operação em cada, em ordem)")
    modo = ap.add_mutually_exclusive_group()
    modo.add_argument("--mapa", action="store_true")
    modo.add_argument("--buscar")
    modo.add_argument("--imagem", metavar="PAGINAS", help="salva as páginas como PNG para leitura visual (gráficos, escaneados)")
    ap.add_argument(
        "--paginas",
        help="ex.: 3-5,9. Sozinho: texto dessas páginas. Com --mapa/--buscar: restringe a elas "
        "(ex.: só a metade em português de um release bilíngue)",
    )
    ap.add_argument("--perfil", choices=sorted(PERFIS), default=None, help="termos do checklist no --mapa")
    ap.add_argument("--tabelas", action="store_true", help="com --paginas: extrai tabelas")
    ap.add_argument("--contexto", type=int, default=0, help="com --buscar: linhas de contexto")
    ap.add_argument("--recorte", help="com --imagem: x0,y0,x1,y1 em frações da página, ex.: 0.45,0,1,1 (metade direita)")
    ap.add_argument("--resolucao", type=int, default=110, help="com --imagem: DPI (padrão 110; suba só se o texto ficar ilegível)")
    ap.add_argument("--max-chars", type=int, default=25000)
    args = ap.parse_args()
    if not (args.mapa or args.buscar or args.imagem or args.paginas):
        ap.error("informe --mapa, --buscar, --imagem ou --paginas")
    if args.imagem and args.paginas:
        ap.error("--imagem já recebe as páginas; não use --paginas junto")

    out = Saida(args.max_chars)
    contagem: Dict[str, Dict[str, int]] = {}
    for arquivo in args.arquivos:
        if not processar(arquivo, args, out, contagem):
            break

    # comparação entre relatórios: quantas linhas citam cada termo em cada arquivo
    if args.buscar and len(contagem) > 1:
        nomes = [t.strip() for t in args.buscar.split(",") if t.strip()]
        arqs = list(contagem)
        sys.stdout.write("\nOcorrências (linhas) por termo e arquivo:\n")
        sys.stdout.write("|Termo|" + "|".join(f"[{i}]" for i in range(1, len(arqs) + 1)) + "|\n")
        sys.stdout.write("|-|" + "|".join("-" for _ in arqs) + "|\n")
        for nome in nomes:
            sys.stdout.write(f"|{nome}|" + "|".join(str(contagem[a].get(nome, 0)) for a in arqs) + "|\n")
        for i, a in enumerate(arqs, 1):
            sys.stdout.write(f"[{i}] {a}\n")


if __name__ == "__main__":
    main()
