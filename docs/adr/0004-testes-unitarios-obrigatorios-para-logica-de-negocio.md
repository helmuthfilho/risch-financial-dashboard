---
número: 0004
título: Testes unitários obrigatórios para lógica de negócio, com coverage mínimo reforçado
status: aceito
criado_em: 2026-08-22
---

# 0004 — Testes unitários obrigatórios para lógica de negócio, com coverage mínimo reforçado

## Status

Aceito

## Contexto

A implementação da spec [[002-renda-fixa]] acabou naturalmente com bastante
teste unitário para a lógica pura (conversão de moeda, validação, cálculo de
totais) — e isso se mostrou valioso: pegou um bug real de arredondamento de
float antes de virar código de produção. O usuário quer formalizar isso como
prática do projeto, não deixar como algo incidental que pode não se repetir
nas próximas specs.

Ao mesmo tempo, o projeto já tem um caminho de validação para UI/integração
via navegador headless (`.claude/skills/run-risch-financial-dashboard/`), e
testar componentes React/Server Actions com mocks pesados de Prisma teria um
custo de tooling alto para um app pessoal — desproporcional ao benefício,
tensionando com [[constitution]] item 6 (simplicidade primeiro).

## Decisão

- **Toda lógica de negócio pura** (utilitários, validação, cálculos —
  hoje `src/lib/**`, exceto arquivos de infraestrutura trivial como o
  singleton do Prisma) **tem teste unitário obrigatório**, escrito na mesma
  task que introduz o código, não depois.
- **Componentes React, páginas e Server Actions não são cobertos por testes
  unitários** — continuam validados via o driver Playwright da skill
  `run-risch-financial-dashboard` (fluxo real no navegador) e revisão manual.
  Se isso mudar (ex.: adotar React Testing Library), é uma nova decisão, não
  uma expansão silenciosa deste ADR.
- **Coverage mínimo de 80%** (linhas, funções, branches e statements) no
  escopo acima, reforçado via `@vitest/coverage-v8` — `npm run
test:coverage` falha se cair abaixo disso. Configurado em
  `vitest.config.mts`.

## Alternativas consideradas

- **Meta informal, sem ferramenta.** Mais simples de configurar, mas sem
  reforço automático a meta tende a ser esquecida sob pressão de prazo —
  rejeitada porque o valor de ter um teste (como o bug de arredondamento
  pego na spec 002) só se realiza se o teste realmente for escrito sempre.
- **Cobrir também componentes/Server Actions.** Mais garantia de ponta a
  ponta, mas exige montar mocks de Prisma e testes de componente — custo de
  tooling que não se paga ainda para um app pessoal de um usuário só;
  revisitar se o projeto crescer em complexidade/colaboradores.

## Consequências

- Toda spec futura que adicionar lógica em `src/lib/` precisa incluir uma
  task de teste unitário correspondente no plano/tasks, não só na
  implementação "se sobrar tempo".
- `npm run test:coverage` roda localmente antes de considerar uma task de
  lógica pura concluída (equivalente a `npm run lint`/`npm run test` já
  usados nas specs anteriores).
- Se um arquivo de lógica pura genuinamente não tiver como ser testado sem
  tocar banco/rede (ex.: `getPositionsWithLatestValue`), ele é excluído
  explicitamente do escopo de coverage em `vitest.config.mts` — a exclusão
  fica visível na config, não escondida atrás de um número agregado
  artificialmente alto.
