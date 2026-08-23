---
número: 002
título: Renda Fixa — Cadastro e Acompanhamento de Posições
plano: docs/plans/002-renda-fixa.md
status: concluído
criado_em: 2026-08-22
atualizado_em: 2026-08-22
---

# 002 — Tasks: Renda Fixa — Cadastro e Acompanhamento de Posições

- [x] 1. Adicionar `FixedIncomeType` (enum) e os models
      `FixedIncomePosition` / `FixedIncomeValueUpdate` em
      `prisma/schema.prisma` (campos `Cents` como `BigInt`, conforme
      [[0003-dinheiro-como-inteiro-em-centavos]]); rodar
      `npx prisma migrate dev` para gerar e aplicar a migração.
- [x] 2. Adicionar `centsToBRL` e `brlToCents` em `src/lib/currency.ts`
      (conversão via string, nunca `float × 100`); testes cobrindo os casos
      do plano (`"1234"`, `"1234.5"`, `"1234,50"`, `"19.99"` → `1999n`).
- [x] 3. Criar `src/lib/renda-fixa/schema.ts` com os schemas zod de
      cadastro/edição de posição e de atualização de valor (campos
      obrigatórios: instituição, tipo, valor aplicado, data de aplicação).
- [x] 4. Criar `src/lib/renda-fixa/queries.ts`: busca de posições com o
      último `valueUpdate` de cada uma, e cálculo de totais (aplicado +
      atual mais recente); testes unitários incluindo posição sem nenhuma
      atualização de valor.
- [x] 5. Criar `src/app/renda-fixa/actions.ts` com as Server Actions
      `createPosition`, `updatePosition`, `deletePosition` e
      `addValueUpdate`, validando com os schemas da task 3 e revalidando
      `/renda-fixa` após cada mutação.
- [x] 6. Criar `src/components/renda-fixa/position-form.tsx` (formulário
      compartilhado entre criação e edição de posição).
- [x] 7. Criar `src/app/renda-fixa/nova/page.tsx`, usando o formulário da
      task 6 com a action `createPosition`.
- [x] 8. Criar `src/app/renda-fixa/[id]/editar/page.tsx`, usando o mesmo
      formulário com a action `updatePosition`, pré-preenchido com os dados
      da posição.
- [x] 9. Criar `src/components/renda-fixa/update-value-form.tsx` (registrar
      uma nova atualização de valor para uma posição existente) e
      `src/components/renda-fixa/delete-position-button.tsx` (exclusão com
      confirmação).
- [x] 10. Criar `src/components/renda-fixa/position-table.tsx`: listagem das
      posições (instituição, tipo, valor aplicado, valor atual mais
      recente, vencimento) com totais agregados no rodapé, e as ações de
      editar / atualizar valor / excluir por linha.
- [x] 11. Substituir `src/app/renda-fixa/page.tsx` (hoje placeholder) por uma
      Server Component que busca os dados via `queries.ts` e renderiza
      `position-table.tsx` + link para "Nova posição".
- [x] 12. Rodar `npm run lint`, `npm run test`, `npm run build` e garantir
      que todos passam.
- [x] 13. Validação manual: usar o driver
      `.claude/skills/run-risch-financial-dashboard/driver.mjs` para rodar
      o fluxo completo (cadastrar → editar → atualizar valor → excluir) e
      confirmar visualmente via screenshot que a listagem e os totais
      refletem cada passo; complementar com uma passada no navegador real.

## Notas de execução

- **`tsconfig.json` `target` subiu de `ES2017` para `ES2020`.** Literais
  `BigInt` (`123n`) não compilam abaixo de ES2020 — `npm run build` só
  passou depois desse ajuste. Efeito colateral esperado e aceitável da
  decisão de [[0003-dinheiro-como-inteiro-em-centavos]].
- **Campo de formulário renomeado de `appliedAmountCents`/`amountCents`
  para `appliedAmount`/`amount`.** O input do formulário carrega uma string
  em reais (`"19.99"`), não em centavos — nomear o campo bruto com sufixo
  `Cents` era enganoso. O schema zod faz a conversão via `.transform()` a
  nível de objeto, renomeando para `appliedAmountCents`/`amountCents` só no
  resultado final (o que já bate com as colunas do Prisma).
- **`src/app/renda-fixa/page.tsx` precisou de `export const dynamic =
"force-dynamic"`.** Sem isso, `next build` pré-renderiza a listagem uma
  única vez como página estática, congelando os dados do momento do build.
  `revalidatePath` nas Server Actions provavelmente resolveria isso via
  revalidação sob demanda, mas `force-dynamic` é mais simples e robusto:
  garante releitura do banco em toda requisição sem depender de lembrar de
  chamar `revalidatePath` em cada mutação futura.
- **Teste de formatação de moeda tinha um espaço não-quebrável (U+00A0)
  escondido.** `Intl.NumberFormat("pt-BR", { style: "currency" })` separa
  "R$" do valor com U+00A0, não um espaço comum — um literal com espaço
  normal no teste nunca dava match, mesmo parecendo idêntico visualmente.
  Resolvido usando `String.fromCharCode(0xa0)` explicitamente nos testes de
  `src/lib/currency.test.ts`, em vez de digitar o caractere literal.
- Validação manual (task 13) rodada com o driver da skill
  `run-risch-financial-dashboard`: cadastro → listagem com totais →
  atualização de valor (histórico preservado, valor aplicado inalterado) →
  edição (formulário pré-preenchido corretamente) → exclusão (volta ao
  estado vazio). Sem erros de console em nenhum passo.
