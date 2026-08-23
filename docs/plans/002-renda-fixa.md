---
número: 002
título: Renda Fixa — Cadastro e Acompanhamento de Posições
spec: docs/specs/002-renda-fixa.md
status: concluído
criado_em: 2026-08-22
atualizado_em: 2026-08-22
---

# 002 — Plano Técnico: Renda Fixa — Cadastro e Acompanhamento de Posições

## Visão geral

Substituir o placeholder de `/renda-fixa` por cadastro, edição, exclusão e
listagem de posições de renda fixa, com um histórico de atualizações de
valor (sem cálculo automático de rendimento). Usa Server Actions do Next.js
sobre duas tabelas novas no Prisma; sem API REST separada.

## Componentes afetados

- **Frontend**: `src/app/renda-fixa/` (listagem, formulário de nova posição,
  formulário de edição), componentes em `src/components/renda-fixa/`.
- **Backend**: Server Actions em `src/app/renda-fixa/actions.ts` (sem rotas
  `/api/`).
- **Banco de dados**: duas tabelas novas via Prisma —
  `FixedIncomePosition` e `FixedIncomeValueUpdate`.
- **Outros**: `src/lib/renda-fixa/schema.ts` (validação zod),
  `src/lib/renda-fixa/queries.ts` (leitura + cálculo de totais).

## Modelo de dados

Segue [[constitution]] item 1 (dinheiro como inteiro em centavos — ver
[[0003-dinheiro-como-inteiro-em-centavos]]) e item 7 (nomes de tabela/campo
em inglês, domínio em português na UI e nos docs).

```prisma
enum FixedIncomeType {
  CDB
  TREASURY_DIRECT
  LCI_LCA
}

model FixedIncomePosition {
  id                 String    @id @default(cuid())
  institution        String
  type               FixedIncomeType
  description        String?
  appliedAt          DateTime
  appliedAmountCents BigInt
  contractedRate     String?
  maturityDate       DateTime?
  createdAt          DateTime  @default(now())
  updatedAt          DateTime  @updatedAt

  valueUpdates       FixedIncomeValueUpdate[]
}

model FixedIncomeValueUpdate {
  id          String              @id @default(cuid())
  position    FixedIncomePosition @relation(fields: [positionId], references: [id], onDelete: Cascade)
  positionId  String
  amountCents BigInt
  asOf        DateTime
  createdAt   DateTime            @default(now())
}
```

Só `institution`, `type`, `appliedAt` e `appliedAmountCents` são
obrigatórios, batendo com os critérios de aceite da spec (os únicos campos
validados como obrigatórios são instituição, tipo, valor aplicado e data de
aplicação). `description`, `contractedRate` e `maturityDate` ficam
opcionais.

"Valor atual" **não** é um campo na posição — é sempre o `amountCents` do
`FixedIncomeValueUpdate` mais recente daquela posição (ou ausente, se nunca
atualizado). Isso evita ter dois lugares guardando o mesmo dado e mantém o
histórico como única fonte da verdade (ver Decisões técnicas).

`src/lib/currency.ts` (criado na spec 001, hoje só com `formatCurrencyBRL`
para exibição) ganha duas funções nesta spec:

- `centsToBRL(cents: bigint): string` — formata centavos como moeda BRL
  para exibição (reaproveita `formatCurrencyBRL` internamente).
- `brlToCents(input: string): bigint` — converte a entrada de formulário
  (string, ex.: `"1234.50"` ou `"1234,50"`) para centavos operando sobre a
  string (parse dos dígitos antes/depois do separador decimal), **nunca**
  `Math.round(Number(input) * 100)` — multiplicar um `float` por 100 pode
  gerar erro de arredondamento (`19.99 * 100 = 1998.9999999997`), que é
  exatamente o problema que centavos existem para evitar.

Toda leitura/escrita de valor monetário nas Server Actions e componentes
passa por essas duas funções — nenhum código de feature faz `× 100`/`÷ 100`
diretamente (ver [[0003-dinheiro-como-inteiro-em-centavos]]).

## Decisões técnicas

| Decisão                                                             | Alternativas consideradas                                                              | Motivo da escolha                                                                                                                                                         |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Server Actions do Next.js, sem rotas `/api/`                        | Rotas REST em `/api/renda-fixa`                                                        | App é single-user local; Server Actions eliminam o boilerplate de rota + fetch client-side, com a mesma validação (zod) rodando no server                                 |
| Zod para validação                                                  | Validação manual (`if`s)                                                               | Tipagem e validação juntas num único schema, compartilhado entre client (feedback imediato) e server (fonte da verdade)                                                   |
| Valor atual calculado em tempo de leitura (sem campo denormalizado) | Campo `valorAtual` cacheado em `FixedIncomePosition`, atualizado junto com o histórico | Volume de dados é baixo (ver requisito não-funcional de desempenho na spec); calcular na leitura evita o risco de cache dessincronizado do histórico e não duplica estado |
| IDs `cuid()`                                                        | Auto-increment inteiro                                                                 | Padrão do Prisma para este tipo de entidade; evita expor contagem de registros                                                                                            |

Nenhuma dessas decisões atravessa outras áreas do dashboard (Renda Variável,
Gastos) o suficiente para virar ADR — ficam registradas aqui. A única
decisão desta spec que _é_ cross-cutting (como armazenar dinheiro) já virou
[[0003-dinheiro-como-inteiro-em-centavos]], não fica só neste plano.

## Riscos e mitigação

- **`BigInt` não serializa em JSON.** Server Actions/props que cruzam a
  fronteira server→client component com um valor `Cents` precisam converter
  explicitamente (string ou number) antes — não dá pra simplesmente
  retornar o objeto do Prisma direto pro client. Mitigação: os componentes
  de UI recebem valores já formatados via `centsToBRL` (string), não o
  `bigint` cru; se algum componente precisar do valor bruto para cálculo no
  client, converter para `string` explicitamente.
- **Cálculo de "valor mais recente por posição" feito em memória** (buscar
  todas as posições com seu último `valueUpdate` via `include` + `take: 1`,
  depois somar em JS) pode não escalar bem com muitos milhares de posições.
  Mitigação: aceitável para uso pessoal (dezenas a centenas, conforme a
  spec); revisitar com uma query SQL agregada (`DISTINCT ON`) só se o volume
  real justificar.
- **Sem autenticação**: qualquer processo com acesso a `localhost:3000` pode
  criar/editar/excluir posições. Mitigação: aceitável — app é single-user
  local por decisão da [[constitution]] (item 4); revisitar se um dia a
  aplicação for exposta fora da máquina do usuário.

## Estratégia de testes

- Casos críticos a cobrir (Vitest, unitário, sem bater no Postgres real):
  - `brlToCents`/`centsToBRL` (`src/lib/currency.ts`): valores com e sem
    centavos (`"1234"`, `"1234.5"`, `"1234.50"`, `"1234,50"`), e
    especificamente casos historicamente propensos a erro de ponto
    flutuante (ex.: `"19.99"` deve virar exatamente `1999n`, não
    `1998n`/`1999.0000000002n`).
  - Schemas zod (`src/lib/renda-fixa/schema.ts`): campos obrigatórios
    ausentes, valor não numérico ou negativo, tipo fora do enum.
  - Cálculo de totais (`src/lib/renda-fixa/queries.ts`): soma de valor
    aplicado e de valor atual mais recente por posição, com posições sem
    nenhuma atualização de valor (não devem quebrar o total).
- Como validar manualmente: usar o driver da skill
  `.claude/skills/run-risch-financial-dashboard/driver.mjs` para rodar o
  fluxo completo no navegador headless — cadastrar uma posição, editar,
  registrar uma atualização de valor, excluir, e conferir que a listagem e
  os totais refletem cada passo — mais uma passada manual no navegador real.

## Plano de tasks

Ver `docs/tasks/002-renda-fixa.md` para a quebra detalhada (a criar).
