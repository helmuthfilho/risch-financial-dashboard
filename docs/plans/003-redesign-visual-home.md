---
número: 003
título: Redesign Visual da Home
spec: docs/specs/003-redesign-visual-home.md
status: concluído
criado_em: 2026-08-23
atualizado_em: 2026-08-23
---

# 003 — Plano Técnico: Redesign Visual da Home

## Visão geral

Redesenhar visualmente `src/app/page.tsx` com uma paleta verde-tecnológica
(tons teal), ícones `lucide-react` nos 3 cards de navegação e um elemento
gráfico decorativo em CSS puro (gradiente + padrão de grid). Os mesmos tokens
de cor são reaproveitados nos estados de destaque de
`src/components/nav/sidebar.tsx` para manter consistência visual. Nenhum
dado, rota ou modelo é alterado — mudança restrita a apresentação.

## Componentes afetados

- **Frontend**: `src/app/page.tsx` (home), `src/components/nav/sidebar.tsx`
  (cores de item ativo/hover), `src/app/globals.css` (novos tokens de cor
  `--color-brand-*` e utilitário de padrão de fundo).
- **Backend / API**: nenhum.
- **Banco de dados**: nenhum.
- **Outros**: `package.json`/`package-lock.json` (nova dependência de
  produção `lucide-react`).

## Modelo de dados

Não aplicável — mudança puramente visual, sem novos campos ou tabelas.

## Decisões técnicas

| Decisão                                                                                                                                                                                                                                                     | Alternativas consideradas                                                                                                      | Motivo da escolha                                                                                                                                                              |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Paleta base "verde-tecnológico com leve toque azulado" implementada como tokens `--color-brand`, `--color-brand-foreground` etc. em `globals.css` (`@theme inline`), usando a escala `teal` do Tailwind como referência de tom, com variante para dark mode | Usar classes utilitárias `emerald-*`/`green-*` diretamente espalhadas pelos componentes; usar `green` puro (sem toque azulado) | Tokens centralizados evitam duplicar valores de cor em vários arquivos e concentram o ajuste de tom num só lugar, seguindo o padrão já usado por `--background`/`--foreground` |
| Ícones dos cards via `lucide-react`: `TrendingUp` (Renda Variável), `PiggyBank` (Renda Fixa), `CreditCard` (Gastos)                                                                                                                                         | `@heroicons/react`, `react-icons`                                                                                              | `lucide-react` é leve, tree-shakeable, sem peer-dependency extra, e é o padrão mais comum em projetos Next.js + Tailwind recentes                                              |
| Elemento decorativo (grid/gradiente) implementado só com CSS (`background-image`/`repeating-linear-gradient` + gradiente radial), aplicado apenas no wrapper da home                                                                                        | SVG inline exportado como componente; asset estático (PNG/SVG) em `public/`                                                    | CSS puro não adiciona peso de rede nem asset novo para gerenciar, e se adapta a dark mode reaproveitando os tokens de cor                                                      |
| Microanimação de hover/foco nos cards via classes Tailwind (`transition-colors`, `transition-shadow`, leve `hover:-translate-y-0.5`)                                                                                                                        | Framer Motion; `@keyframes` CSS customizada                                                                                    | Spec exige explicitamente não introduzir lib de animação nova; Tailwind já cobre transições simples                                                                            |
| Sidebar: troca das classes atuais de item ativo/hover (`bg-black/10 dark:bg-white/15`, `hover:bg-black/5 dark:hover:bg-white/10`) pelos tokens `--color-brand-*`                                                                                            | Manter sidebar em cinza neutro e colorir só a home                                                                             | Requisito funcional 7 da spec pede consistência visual entre home e sidebar                                                                                                    |
| Contraste de texto sobre fundo verde/gradiente conferido manualmente (via inspeção de cor/contraste no navegador) antes de fechar os tokens, em ambos os temas                                                                                              | Confiar só em inspeção visual sem checar razão de contraste                                                                    | Requisito não-funcional da spec exige nível AA (WCAG) explicitamente                                                                                                           |

Nenhuma dessas decisões atravessa outras features além desta home/sidebar —
não há necessidade de ADR novo.

## Riscos e mitigação

- **Tom de verde não agradar visualmente** ("verde-tecnológico" é subjetivo):
  mitigado validando com captura de tela via skill `run-risch-financial-dashboard`
  em modo claro e escuro antes de considerar a task pronta; como a cor vive em
  poucos tokens centralizados, ajustar é barato.
- **Cor nova na sidebar reduzir contraste do item ativo em dark mode**:
  mitigado testando visualmente os dois temas e mantendo o texto usando
  `--foreground`/`--brand-foreground` conforme o que garantir mais contraste.
- **Dependência nova (`lucide-react`) aumentar o bundle**: mitigado por import
  nomeado (tree-shaking automático do bundler do Next) — apenas 3 ícones são
  usados, impacto desprezível.

## Estratégia de testes

- **Casos críticos a cobrir com teste unitário**: nenhum. A mudança é 100%
  em componentes/página (`page.tsx`, `sidebar.tsx`, `globals.css`), fora do
  escopo de `src/lib/**` — não introduz lógica de negócio pura (ver
  [[constitution]] item 8).
- **Como validar manualmente**: usar o driver de navegador da skill
  `run-risch-financial-dashboard` para abrir `/` e conferir, em modo claro e
  escuro: paleta verde-tecnológica aplicada; os 3 cards com ícone e destino
  corretos (`/renda-variavel`, `/renda-fixa`, `/gastos`); elemento decorativo
  visível sem prejudicar a leitura; microanimação de hover funcionando;
  sidebar com a mesma paleta no item ativo/hover. Rodar `npm run lint` (e o
  build, se aplicável) para garantir ausência de erros de tipo/importação.

## Plano de tasks

Ver `docs/tasks/003-redesign-visual-home.md` (a criar).
