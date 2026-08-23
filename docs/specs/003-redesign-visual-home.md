---
número: 003
título: Redesign Visual da Home
status: concluído
criado_em: 2026-08-23
atualizado_em: 2026-08-23
---

# 003 — Redesign Visual da Home

## Contexto e motivação

A home atual (`/`) é puramente funcional: um título, uma frase de apoio e um
grid de 3 cards de texto que levam às áreas do dashboard (Renda Variável,
Renda Fixa, Gastos). Não há identidade visual que remeta ao domínio da
aplicação — um dashboard financeiro com pegada tecnológica. O usuário quer
que a home passe a comunicar isso visualmente, com uma paleta em tons de
verde, sem alterar a navegação nem os dados exibidos.

## Objetivo

Dar à home uma identidade visual moderna, com tema "financeiro + tecnologia"
em tons de verde, mantendo a estrutura de navegação atual (3 seções) e sem
introduzir dados ou funcionalidades novas.

## Escopo

### Dentro do escopo

- Nova paleta de cores em tons de verde, definida como tokens CSS em
  `src/app/globals.css`, com variantes para modo claro e escuro.
- Redesign visual da página `/` (`src/app/page.tsx`): título, subtítulo e os
  3 cards de navegação (Renda Variável, Renda Fixa, Gastos), incluindo
  elementos gráficos com tema "financeiro + tecnologia" (ícones, gradiente
  sutil, padrão de fundo tipo grid/linhas) e microanimações leves de
  hover/foco nos cards.
- Adição da biblioteca `lucide-react` para os ícones de cada card e de
  eventuais elementos decorativos.
- Ajuste pontual das cores de destaque da sidebar
  (`src/components/nav/sidebar.tsx`) para a mesma paleta verde (ex.: item
  ativo, hover), garantindo consistência visual com a nova home — sem
  alterar sua estrutura de itens ou comportamento de navegação.
- Suporte a modo claro/escuro consistente com o padrão já usado no projeto
  (`prefers-color-scheme`).

### Fora do escopo

- Alteração de conteúdo ou layout das páginas Renda Variável, Renda Fixa e
  Gastos.
- Qualquer dado dinâmico ou resumo financeiro na home (ex.: patrimônio total,
  saldo do mês) — a mudança é puramente visual/estrutural, sem novos dados.
- Redesenho estrutural da sidebar (itens, hierarquia, responsividade,
  comportamento) — só a paleta de cores de destaque muda.
- Toggle manual de tema claro/escuro — continua seguindo a preferência do
  sistema operacional, como hoje.
- Troca de fontes (mantém Geist Sans/Geist Mono já configuradas).
- Multi-usuário, autenticação, integrações externas — já fora de escopo pela
  constituição (ver [[constitution]] seção 3); não tensionado aqui.

## Requisitos funcionais

1. A home (`/`) exibe uma nova composição visual usando tons de verde
   tecnológico (verde com leve toque azulado, ex.: família teal) como cor de
   destaque primária.
2. Os 3 links de navegação existentes continuam presentes, com os mesmos
   destinos (`/renda-variavel`, `/renda-fixa`, `/gastos`) e os mesmos rótulos
   e descrições atuais (ou equivalentes), apenas com novo tratamento visual.
3. Cada card de navegação exibe um ícone representativo do tema (via
   `lucide-react`): gráfico de tendência para Renda Variável, cofre/moeda
   para Renda Fixa e cartão para Gastos.
4. A home inclui ao menos um elemento gráfico decorativo com tema
   "financeiro + tecnologia" (ex.: gradiente verde sutil, padrão de fundo
   tipo grid/linhas), sem comprometer a legibilidade do texto sobre ele.
5. Os cards de navegação têm uma microanimação leve de hover/foco (ex.:
   transição de cor, sombra ou escala), implementada apenas com CSS/Tailwind,
   sem biblioteca de animação adicional.
6. A paleta de verde é aplicada tanto no modo claro quanto no modo escuro,
   com contraste de texto adequado em ambos.
7. A sidebar adota a mesma paleta de verde em seus elementos de destaque
   (ex.: item ativo, hover), sem alterar sua estrutura de itens ou
   comportamento de navegação.
8. Nenhum dado financeiro real ou fictício passa a ser exibido na home como
   parte desta mudança.

## Requisitos não-funcionais

- Desempenho / volume de dados esperado: sem impacto perceptível no
  carregamento; ícones importados de forma otimizada (import nomeado do
  `lucide-react`, que suporta tree-shaking); preferir CSS/SVG a imagens
  pesadas para os elementos decorativos.
- Segurança / privacidade (ver [[constitution]] item 2): não aplicável de
  forma direta — a mudança é puramente visual e não manipula dados
  financeiros, de conta ou de transação.
- Acessibilidade: contraste de texto sobre fundo verde/gradiente deve
  atender no mínimo o nível AA do WCAG, em ambos os temas (claro e escuro).
- Outros: manter a responsividade atual da home (grid que se adapta de 1
  coluna em mobile para 3 em telas maiores).

## Critérios de aceite

- [ ] A página `/` usa uma paleta de tons de verde como cor de destaque,
      visível tanto no modo claro quanto no escuro.
- [ ] Os 3 cards de navegação continuam levando aos mesmos destinos atuais,
      agora com ícone (`lucide-react`) e novo tratamento visual.
- [ ] A home tem ao menos um elemento gráfico decorativo (gradiente e/ou
      padrão de fundo) sem prejuízo de legibilidade.
- [ ] Os cards têm microanimação de hover/foco via CSS/Tailwind.
- [ ] A sidebar usa a mesma paleta verde em seus elementos de destaque (ex.:
      item ativo/hover), mantendo estrutura e comportamento inalterados.
- [ ] `lucide-react` foi adicionado como dependência e é usado nos ícones dos
      cards.
- [ ] Nenhuma outra página (Renda Variável, Renda Fixa, Gastos) teve seu
      visual alterado por esta mudança.
- [ ] Mudança validada visualmente em modo claro e escuro via o driver de
      navegador da skill `run-risch-financial-dashboard`.

## Desvios da constituição

Nenhum. A mudança é puramente visual: não introduz `float`/`Decimal` para
dinheiro (não mexe em valores monetários), não expõe dados financeiros
sensíveis, não altera a auditabilidade de saldo/posição, não adiciona
multi-usuário ou integração externa, e é implementável com uma dependência
nova pequena e amplamente usada (`lucide-react`), justificada pelo pedido
explícito de elementos gráficos ricos — mantendo o princípio de simplicidade
ao evitar bibliotecas de animação ou motion adicionais.

## Perguntas em aberto

Nenhuma. Ícones por seção e tom de verde foram definidos (ver requisitos
funcionais 1 e 3); o valor exato do token de cor (hex/HSL) fica a critério do
plano técnico.
