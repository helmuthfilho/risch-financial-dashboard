#!/usr/bin/env python3
"""Abre um Pull Request no GitHub para uma feature do fluxo SDD, via `gh`.

Só cuida da parte mecânica: valida a branch, commita mudanças pendentes se
mandarem uma mensagem, dá push e chama `gh pr create`. Quem decide título e
corpo do PR (a partir de docs/specs|plans|tasks/NNN-nome.md e do que foi
validado na sessão) é quem chama este script — ele não lê nem interpreta
esses arquivos, só recebe título e um arquivo de corpo já prontos.

Nunca commita sem --commit-message explícito, nunca força push, nunca abre
PR de uma branch para ela mesma, nunca faz merge.
"""

from __future__ import annotations

import argparse
import subprocess
import sys


def run(cmd: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=capture)


def capture_or_die(cmd: list[str]) -> str:
    result = run(cmd, capture=True)
    if result.returncode != 0:
        sys.exit(f"erro ao rodar `{' '.join(cmd)}`:\n{result.stderr.strip()}")
    return result.stdout.strip()


def run_or_die(cmd: list[str], dry_run: bool) -> None:
    print(f"$ {' '.join(cmd)}")
    if dry_run:
        print("  (--dry-run: não executado)")
        return
    result = run(cmd, capture=True)
    if result.returncode != 0:
        sys.exit(f"`{' '.join(cmd)}` falhou:\n{result.stderr.strip()}")
    if result.stdout.strip():
        print(result.stdout.strip())


def detect_base_branch() -> str:
    result = run(
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], capture=True
    )
    if result.returncode == 0 and result.stdout.strip():
        ref = result.stdout.strip()
        return ref[len("origin/") :] if ref.startswith("origin/") else ref
    return "main"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--title", required=True, help="Título do PR (e do commit, se precisar commitar)")
    parser.add_argument(
        "--body-file",
        required=True,
        help="Caminho de um arquivo markdown com o corpo do PR já pronto, seguindo assets/pr_template.md",
    )
    parser.add_argument(
        "--base",
        default=None,
        help="Branch base (default: detectada via origin/HEAD, fallback 'main')",
    )
    parser.add_argument("--head", default=None, help="Branch de origem (default: branch atual)")
    parser.add_argument(
        "--commit-message",
        default=None,
        help="Mensagem de commit. Obrigatória se houver mudança não commitada — o script nunca inventa uma.",
    )
    parser.add_argument("--draft", action="store_true", help="Abre o PR como draft")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra os comandos que rodaria, sem commitar, pushar ou criar o PR",
    )
    args = parser.parse_args()

    base = args.base or detect_base_branch()
    head = args.head or capture_or_die(["git", "branch", "--show-current"])

    if not head:
        sys.exit("HEAD destacado (detached) — não dá pra abrir PR sem estar numa branch.")
    if head == base:
        sys.exit(
            f"a branch atual ({head!r}) é igual à branch base ({base!r}) — "
            "nunca abra um PR de uma branch para ela mesma."
        )

    auth = run(["gh", "auth", "status"], capture=True)
    if auth.returncode != 0:
        sys.exit("`gh` não está autenticado neste ambiente. Rode `gh auth login` antes de tentar de novo.")

    status = capture_or_die(["git", "status", "--porcelain"])
    if status:
        if not args.commit_message:
            sys.exit(
                "há mudanças não commitadas em "
                f"{head!r} e nenhum --commit-message foi passado. Passe "
                "--commit-message explicitamente em vez de eu adivinhar uma mensagem."
            )
        print(f"Commitando mudanças pendentes em {head!r}...")
        run_or_die(["git", "add", "-A"], args.dry_run)
        run_or_die(["git", "commit", "-m", args.commit_message], args.dry_run)
    else:
        print("Nada pendente para commitar — usando o que já está commitado.")

    print(f"Enviando {head!r} para origin...")
    run_or_die(["git", "push", "-u", "origin", head], args.dry_run)

    gh_cmd = [
        "gh",
        "pr",
        "create",
        "--base",
        base,
        "--head",
        head,
        "--title",
        args.title,
        "--body-file",
        args.body_file,
    ]
    if args.draft:
        gh_cmd.append("--draft")

    print("Abrindo o PR...")
    if args.dry_run:
        print(f"$ {' '.join(gh_cmd)}")
        print("  (--dry-run: nada foi commitado, pushado ou criado)")
        return

    result = run(gh_cmd, capture=True)
    if result.returncode != 0:
        sys.exit(f"`gh pr create` falhou:\n{result.stderr.strip()}")
    print(result.stdout.strip())


if __name__ == "__main__":
    main()
