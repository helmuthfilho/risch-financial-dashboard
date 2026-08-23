# Dashboard Financeiro Pessoal

Aplicação para gerenciar portfólio financeiro pessoal: renda variável, renda
fixa e fluxo de caixa (cartão de crédito, PIX, gastos categorizados).

## Processo: Spec-Driven Development

Este projeto segue um fluxo leve de SDD, documentado em `docs/sdd/`. **Leia
`docs/sdd/workflow.md` e `docs/sdd/constitution.md` antes de propor ou
implementar qualquer funcionalidade nova.**

Resumo do fluxo:

```
docs/specs/NNN-nome.md  →  docs/plans/NNN-nome.md  →  docs/tasks/NNN-nome.md  →  código
```

Regras práticas para o assistente:

- Para qualquer funcionalidade não-trivial (nova tela, novo tipo de ativo,
  mudança de modelo de dados, integração externa): **não pule para código**.
  Primeiro proponha/escreva a spec (`docs/specs/`, usando `_template.md`),
  depois o plano técnico (`docs/plans/`), depois quebre em tasks
  (`docs/tasks/`) — e só então implemente.
- Bug fixes pontuais, typos e ajustes triviais podem ir direto para o código.
- Decisões arquiteturais que atravessam mais de uma feature (escolha de banco
  de dados, framework, estratégia de autenticação etc.) viram um ADR em
  `docs/adr/`, não ficam soterradas num plano específico.
- Novo termo de domínio (ex.: "provento", "posição") → adicionar em
  `docs/sdd/glossary.md`.
- Toda spec deve respeitar `docs/sdd/constitution.md`; se tensionar algum
  princípio, isso vai na seção "Desvios da constituição" da própria spec, não
  fica implícito.
- Numeração de spec/plano/tasks é compartilhada: o mesmo `NNN-nome` percorre os
  três arquivos do mesmo tema.

## Princípios não-negociáveis (ver constituição completa)

- Dinheiro nunca é `float`/`double`/`Decimal` — sempre `bigint` em centavos
  (campos terminam em `Cents`), conversão só via `src/lib/currency.ts`.
- Dados financeiros não são logados em texto claro nem commitados como
  exemplo real.
- Toda mudança de saldo/posição é rastreável a uma transação — sem edição
  silenciosa de agregados.
- Aplicação é local-first, usuário único, sem execução real de ordens.
- Lógica de negócio pura (`src/lib/**`, exceto infra trivial) sempre tem
  teste unitário, escrito junto com o código — não depois. Rode
  `npm run test:coverage` antes de considerar a task pronta (mínimo 80%,
  reforçado por threshold). Componentes/páginas/Server Actions ficam de
  fora desse escopo — validados via o driver de navegador da skill
  `run-risch-financial-dashboard`, não por teste unitário.

## Stack

Definida em [[0002-stack-tecnologica]] (`docs/adr/0002-stack-tecnologica.md`):
Next.js (App Router) + TypeScript, Tailwind CSS, PostgreSQL local via Docker
Compose, Prisma como ORM, Vitest para testes.

@AGENTS.md
