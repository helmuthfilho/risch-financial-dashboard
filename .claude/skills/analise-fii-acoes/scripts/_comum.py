"""Infra compartilhada pelos scripts da skill analise-fii-acoes.

Só biblioteca padrão (Python >= 3.9): leitura do .env, HTTP com cache em
disco, leitura de CSV dentro de ZIP da CVM, conversão de valores para inteiro
escalado e formatação compacta de tabelas (o objetivo é gastar poucos tokens
na saída).

Dinheiro segue a constituição do projeto: nunca vira float. Valores
monetários são lidos da string original direto para inteiro em centavos
(`to_cents`) ou, para valores por cota/ação com muitas casas, para inteiro
em 1e-8 de real (`to_scaled_int(s, 8)`). Float só aparece em razões
(margens, percentuais), que não são dinheiro.
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[4]
CACHE_DIR = Path(os.environ.get("ANALISE_CACHE_DIR", REPO_ROOT / ".cache" / "analise-fii-acoes"))
USER_AGENT = "Mozilla/5.0 (analise-fii-acoes; uso pessoal)"

csv.field_size_limit(sys.maxsize)


# --------------------------------------------------------------------- env


def load_env(path: Optional[Path] = None) -> None:
    """Carrega KEY=VALUE do .env da raiz sem sobrescrever o ambiente atual."""
    env_path = path or REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


def die(msg: str, code: int = 1) -> None:
    print(f"erro: {msg}", file=sys.stderr)
    sys.exit(code)


def warn(msg: str) -> None:
    print(f"aviso: {msg}", file=sys.stderr)


# -------------------------------------------------------------------- http


class HttpError(Exception):
    def __init__(self, status: int, body: bytes):
        super().__init__(f"HTTP {status}")
        self.status = status
        self.body = body


def http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 60, retries: int = 3) -> bytes:
    """GET com User-Agent e retry simples. Nunca loga headers (podem ter token)."""
    req_headers = {"User-Agent": USER_AGENT}
    req_headers.update(headers or {})
    last: Optional[Exception] = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            body = e.read() if hasattr(e, "read") else b""
            if e.code < 500 and e.code != 429:
                raise HttpError(e.code, body) from None
            last = HttpError(e.code, body)
        except OSError as e:  # URLError, socket.timeout, conexão resetada
            last = e
        time.sleep(2 * (attempt + 1))
    assert last is not None
    raise last


def cache_path(*parts: str) -> Path:
    p = CACHE_DIR.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def is_fresh(path: Path, max_age_s: float) -> bool:
    return path.exists() and (time.time() - path.stat().st_mtime) < max_age_s


def download_cached(url: str, dest: Path, max_age_s: float, headers: Optional[Dict[str, str]] = None) -> Optional[Path]:
    """Baixa `url` para `dest` se o arquivo não existir ou estiver velho.

    Retorna None em 404 (ex.: ZIP do ano corrente ainda não publicado). Se o
    download falhar mas houver cópia antiga, usa a cópia antiga com aviso.
    """
    if is_fresh(dest, max_age_s):
        return dest
    try:
        data = http_get(url, headers=headers, timeout=300)
    except HttpError as e:
        if e.status == 404:
            return dest if dest.exists() else None
        if dest.exists():
            warn(f"falha ao atualizar {url} ({e}); usando cache de {time.ctime(dest.stat().st_mtime)}")
            return dest
        raise
    except Exception as e:  # noqa: BLE001 - rede instável: cai para o cache
        if dest.exists():
            warn(f"falha ao atualizar {url} ({e}); usando cache antigo")
            return dest
        raise
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(dest)
    return dest


def cvm_max_age(year: int) -> float:
    """Ano corrente muda toda semana; anos anteriores quase nunca."""
    return 24 * 3600 if year >= time.localtime().tm_year - 1 else 30 * 24 * 3600


def json_cache_get(path: Path, max_age_s: float):
    if is_fresh(path, max_age_s):
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def json_cache_put(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


# -------------------------------------------------------------- csv da CVM


def iter_zip_csv(
    zip_path: Path,
    member: str,
    prefilter: Optional[Callable[[str], bool]] = None,
) -> Iterator[Dict[str, str]]:
    """Itera linhas (dict) de um CSV `;` latin-1 dentro de um ZIP da CVM.

    `prefilter` recebe a linha crua e evita o parse de CSV nas linhas que não
    interessam — é o que deixa varrer arquivos de 100 MB em segundos.
    """
    with zipfile.ZipFile(zip_path) as zf:
        if member not in zf.namelist():
            return
        with zf.open(member) as fh:
            text = io.TextIOWrapper(fh, encoding="latin-1", newline="")
            header = next(csv.reader([text.readline()], delimiter=";"))
            for line in text:
                if prefilter is not None and not prefilter(line):
                    continue
                values = next(csv.reader([line], delimiter=";"))
                yield dict(zip(header, values))


def latest_version(rows: Iterable[Dict[str, str]], key_fields: Sequence[str], version_field: str) -> List[Dict[str, str]]:
    """Mantém só a maior versão de cada documento (reapresentações da CVM)."""
    rows = list(rows)
    best: Dict[tuple, int] = {}
    for r in rows:
        k = tuple(r[f] for f in key_fields)
        best[k] = max(best.get(k, 0), int(r[version_field] or 0))
    return [r for r in rows if int(r[version_field] or 0) == best[tuple(r[f] for f in key_fields)]]


def only_digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())


# ------------------------------------------------------- números e formato


def to_scaled_int(s: Optional[str], decimals: int) -> Optional[int]:
    """Converte string decimal ("123.45", "-1,5", "2.5E-05") em inteiro * 10^decimals.

    Arredonda meio-para-cima no dígito seguinte. Não passa por float.
    """
    if s is None:
        return None
    s = s.strip()
    if not s:
        return None
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    neg = s.startswith("-")
    s = s.lstrip("+-")
    exp = 0
    if "e" in s.lower():
        mant, e = s.lower().split("e", 1)
        s, exp = mant, int(e)
    int_part, _, frac = s.partition(".")
    digits = (int_part or "0") + frac
    point = len(int_part or "0") + exp  # posição da vírgula em `digits`
    shift = point + decimals
    if shift <= 0:
        kept, nxt = "0", (digits[0] if shift == 0 and digits else "0")
    else:
        padded = digits + "0" * max(0, shift + 1 - len(digits))
        kept, nxt = padded[:shift], padded[shift]
    value = int(kept or "0") + (1 if nxt >= "5" else 0)
    return -value if neg and value else value


def to_cents(s: Optional[str]) -> Optional[int]:
    return to_scaled_int(s, 2)


def to_ratio(s: Optional[str]) -> Optional[float]:
    """Percentual/razão (não é dinheiro): float é aceitável."""
    if s is None or not s.strip():
        return None
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b


def fmt_num(x: Optional[float], decimals: int = 1) -> str:
    if x is None:
        return "-"
    s = f"{x:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_mi(cents: Optional[int]) -> str:
    """Centavos -> milhões de reais (1 casa abaixo de R$ 1 bi, inteiro acima)."""
    if cents is None:
        return "-"
    mi = cents / 1e8
    return fmt_num(mi, 0 if abs(mi) >= 1000 else 1)


def fmt_brl(cents: Optional[int]) -> str:
    return "-" if cents is None else fmt_num(cents / 100, 2)


def fmt_pct(ratio: Optional[float], decimals: int = 1) -> str:
    """Razão (0,0123) -> "1,2%"."""
    return "-" if ratio is None else fmt_num(ratio * 100, decimals) + "%"


def print_table(headers: Sequence[str], rows: Sequence[Sequence[str]], out=None) -> None:
    """Tabela markdown mínima (sem alinhamento com espaços = menos tokens)."""
    out = out or sys.stdout
    out.write("|" + "|".join(headers) + "|\n")
    out.write("|" + "|".join("-" for _ in headers) + "|\n")
    for r in rows:
        out.write("|" + "|".join(str(c) for c in r) + "|\n")


def quarter_label(date_iso: str) -> str:
    """"2026-06-30" -> "2T26"."""
    y, m = int(date_iso[:4]), int(date_iso[5:7])
    return f"{(m - 1) // 3 + 1}T{str(y)[2:]}"
