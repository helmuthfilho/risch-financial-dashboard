---
número: 0001
título: Adotar estrutura leve de Spec-Driven Development
status: aceito
criado_em: 2026-08-22
---

# 0001 — Adotar estrutura leve de Spec-Driven Development

## Status

Aceito

## Contexto

O projeto é um dashboard financeiro pessoal (renda variável, renda fixa,
gastos de cartão/PIX) construído do zero. O usuário quer seguir um processo de
Spec-Driven Development (SDD) — escrever specs antes de implementar — mas sem
adotar uma ferramenta externa com opinião forte sobre estrutura/comandos.

## Decisão

Usar uma estrutura de pastas própria, sem dependências externas:
`docs/sdd/` (constituição, glossário, fluxo), `docs/specs/`, `docs/plans/`,
`docs/tasks/`, `docs/adr/`, cada uma com um template `_template.md`. Um
`CLAUDE.md` na raiz ensina o assistente a seguir esse fluxo automaticamente.

## Alternativas consideradas

- **GitHub Spec-Kit** — ferramenta oficial com comandos `/specify`, `/plan`,
  `/tasks`. Rejeitada por enquanto: adiciona uma dependência externa (instalação
  via `uvx`/`pip`) e uma convenção mais rígida do que o necessário para um
  projeto pessoal em estágio inicial. Pode ser revisitada mais tarde se o
  projeto crescer em complexidade/colaboradores.

## Consequências

- Fica mais fácil adaptar o processo às necessidades específicas do projeto
  (ex.: seção "Desvios da constituição" nas specs).
- Fica mais difícil aproveitar tooling/automação pronta que ferramentas como o
  Spec-Kit oferecem — se isso se tornar necessário, migrar exige esforço manual.
