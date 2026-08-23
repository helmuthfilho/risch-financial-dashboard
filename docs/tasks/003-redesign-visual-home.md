---
número: 003
título: Redesign Visual da Home
plano: docs/plans/003-redesign-visual-home.md
status: concluído
criado_em: 2026-08-23
atualizado_em: 2026-08-23
---

# 003 — Tasks: Redesign Visual da Home

Cada task deve ser pequena o suficiente para revisar em um único diff, e em
ordem de execução.

- [x] 1. Definir os tokens de cor da paleta verde-tecnológica
      (`--color-brand`, `--color-brand-foreground` e variantes necessárias)
      em `src/app/globals.css`, com valores para modo claro e escuro,
      seguindo o mesmo padrão já usado por `--background`/`--foreground`
      (`:root` + bloco `@media (prefers-color-scheme: dark)`, expostos via
      `@theme inline`).
- [x] 2. Adicionar `lucide-react` como dependência de produção
      (`npm install lucide-react`).
- [x] 3. Redesenhar `src/app/page.tsx`: nova composição visual usando os
      tokens da task 1, ícones `TrendingUp` (Renda Variável), `PiggyBank`
      (Renda Fixa) e `CreditCard` (Gastos) de `lucide-react` em cada card,
      um elemento decorativo em CSS puro (gradiente + padrão de
      grid/linhas via `repeating-linear-gradient`) e microanimação de
      hover/foco nos cards via classes Tailwind — mantendo os mesmos 3
      destinos (`/renda-variavel`, `/renda-fixa`, `/gastos`) e a
      responsividade atual (1 coluna em mobile, 3 em telas maiores).
- [x] 4. Atualizar `src/components/nav/sidebar.tsx`: trocar as classes de
      item ativo (`bg-black/10 dark:bg-white/15`) e hover
      (`hover:bg-black/5 dark:hover:bg-white/10`) pelos tokens
      `--color-brand-*` da task 1, sem alterar a estrutura de itens ou o
      comportamento de navegação.
- [x] 5. Rodar `npm run lint` e `npm run build`, garantindo que passam sem
      erros (sem `npm run test`/`test:coverage` nesta feature — não há
      lógica nova em `src/lib/**`).
- [x] 6. Validação manual: usar o driver
      `.claude/skills/run-risch-financial-dashboard/driver.mjs` para abrir
      `/` em modo claro e escuro, confirmar visualmente via screenshot a
      paleta verde-tecnológica, os ícones e destinos corretos dos 3 cards,
      o elemento decorativo sem prejuízo de legibilidade, a microanimação
      de hover e a paleta consistente aplicada na sidebar.

## Notas de execução

- **Tokens definidos** (light/dark) em `src/app/globals.css`: `--brand`
  (teal-600 `#0d9488` / teal-400 `#2dd4bf`), `--brand-strong` (teal-700
  `#0f766e` / teal-300 `#5eead4`), `--brand-foreground` (`#ffffff` /
  `#042f2e`), expostos via `@theme inline` como `--color-brand`,
  `--color-brand-strong`, `--color-brand-foreground`. Combinações escolhidas
  para atender AA (contraste ≥ 4.5:1 texto normal / ≥ 3:1 texto grande e
  elementos gráficos) em ambos os temas — conferido por cálculo manual antes
  de implementar.
- **Elemento decorativo**: classe `.hero-pattern` em `globals.css`
  (`@layer components`), combinando um `radial-gradient` sutil com dois
  `repeating-linear-gradient` (grid) via `color-mix()` sobre `var(--brand)`,
  que se adapta automaticamente a light/dark por depender só desse token.
- **Driver de navegador não emulava `prefers-color-scheme`** — editar CSS
  vars via `eval` não ativa as classes `dark:` do Tailwind (que dependem da
  media query real, não das custom properties). Adicionado o comando
  `emulate-color-scheme <light|dark>` a
  `.claude/skills/run-risch-financial-dashboard/driver.mjs`, usando
  `page.emulateMedia({ colorScheme })` do Playwright, para permitir
  validação real dos dois temas.
- Validação manual: screenshots da home em modo claro e escuro (paleta,
  ícones dos 3 cards, elemento decorativo, cards) e da página `/renda-fixa`
  em modo escuro (item ativo da sidebar com `bg-brand-strong` +
  `text-brand-foreground`, contraste adequado). Sem erros de console em
  nenhum passo.
