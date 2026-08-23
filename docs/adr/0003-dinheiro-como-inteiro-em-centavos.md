---
número: 0003
título: Dinheiro armazenado como inteiro em centavos (bigint)
status: aceito
criado_em: 2026-08-22
---

# 0003 — Dinheiro armazenado como inteiro em centavos (bigint)

## Status

Aceito

## Contexto

[[constitution]] (item 1) já exige que dinheiro nunca seja `float`/`double`,
mas deixava em aberto qual tipo decimal exato usar — citava `Decimal` e
"inteiros em centavos" como exemplos equivalentes. Ao desenhar o modelo de
dados da spec [[002-renda-fixa]] ([[002-renda-fixa (plano)|docs/plans/002-renda-fixa.md]]),
essa ambiguidade apareceu na prática: `Decimal`/`numeric(14,2)` e `bigint`
em centavos são ambos exatos, mas têm trade-offs diferentes de ergonomia de
código. Como todo valor monetário do projeto (Renda Fixa, Renda Variável,
Gastos) vai precisar dessa mesma escolha, faz sentido travar um padrão único
agora em vez de decidir de novo a cada spec.

## Decisão

Todo valor monetário é armazenado como **inteiro em centavos**
(`bigint` no Postgres/Prisma), nunca como `numeric`/`Decimal` nem
`float`/`double`. Exemplo: R$ 1.234,50 é armazenado como `123450`.

Nomes de campo que guardam dinheiro sempre terminam em `Cents` (ex.:
`appliedAmountCents`, `amountCents`), para deixar a unidade explícita e
evitar que alguém some um valor em centavos com um valor em reais por
engano.

Conversão entre centavos e reais é centralizada em utilitários em
`src/lib/currency.ts` (ex.: `centsToBRL` para exibição, `brlToCents` para
converter entrada de formulário) — nenhum código de feature faz `× 100` ou
`÷ 100` diretamente. A conversão de entrada de usuário (string digitada) para
centavos deve operar sobre a string, não multiplicar um `float` por 100
(`"19.99" * 100` pode gerar `1998.9999999997` em ponto flutuante) — do
contrário reintroduzimos o mesmo problema que essa decisão existe pra evitar.

## Alternativas consideradas

- **`Decimal`/`numeric(14,2)`** (Prisma `Decimal`, Postgres `numeric`): também
  exato, e mais simples no código (nenhuma conversão manual, o valor no banco
  já é a quantia em reais, legível direto numa query). Era o plano original
  da spec 002. Rejeitado em favor de centavos: é a convenção que o usuário
  já usa mentalmente vindo de outras integrações (Stripe-like), e evita
  qualquer ambiguidade de arredondamento em somas/relatórios agregados, ao
  custo de exigir os utilitários de conversão citados acima.

## Consequências

- Todo schema Prisma novo com campo monetário usa `BigInt` + sufixo `Cents`.
- `src/lib/currency.ts` (já existe, criado na spec 001 só com formatação de
  exibição) ganha as funções de conversão `centsToBRL`/`brlToCents` como
  parte da spec 002, e vira dependência obrigatória de qualquer spec futura
  que lide com dinheiro.
- `BigInt` não serializa nativamente em `JSON.stringify` — Server
  Actions/rotas que retornam valores monetários precisam converter para
  string ou number de forma explícita antes de cruzar a fronteira
  server/client.
- Consultas agregadas (somas, totais) continuam exatas porque somar inteiros
  nunca perde precisão, diferente de somar `float`.
