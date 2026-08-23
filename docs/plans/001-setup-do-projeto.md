---
número: 001
título: Setup do Projeto
spec: docs/specs/001-setup-do-projeto.md
status: concluído
criado_em: 2026-08-22
atualizado_em: 2026-08-22
---

# 001 — Plano Técnico: Setup do Projeto

## Visão geral

Inicializar um projeto Next.js (App Router) + TypeScript, subir PostgreSQL
local via Docker Compose, conectar via Prisma, e criar o layout base com
navegação entre as 3 áreas do dashboard. Stack definida em [[0002-stack-tecnologica]].

## Componentes afetados

- **Frontend**: novo — Next.js App Router, layout com sidebar/nav, 3 páginas
  placeholder (`/renda-variavel`, `/renda-fixa`, `/gastos`).
- **Backend / API**: novo — uma rota de health check (`/api/health`) que
  testa a conexão com o banco.
- **Banco de dados**: novo — Postgres via Docker Compose, schema Prisma
  inicial vazio (sem tabelas de domínio ainda — isso é escopo das próximas
  specs).
- **Ferramentas**: ESLint, Prettier, Vitest (testes).

## Modelo de dados

Nenhuma tabela de domínio nesta etapa. O `schema.prisma` inicial só declara o
`datasource` (Postgres) e o `generator` (Prisma Client) — a primeira migração
é vazia, apenas para validar que a conexão e o fluxo de migração funcionam.
Tabelas de domínio (ativos, posições, transações) entram nas specs `002+`,
respeitando "dinheiro nunca é float" ([[constitution]]): valores monetários
como `Decimal` no Prisma (mapeado para `numeric` no Postgres).

## Decisões técnicas

| Decisão                      | Alternativas consideradas     | Motivo da escolha                                                                           |
| ----------------------------- | ------------------------------ | --------------------------------------------------------------------------------------------- |
| Next.js App Router           | Pages Router                  | App Router é o padrão atual, melhor suporte a layouts aninhados (útil para a sidebar)       |
| Docker Compose para Postgres | Instalação nativa do Postgres | Reprodutível, isolado, fácil de destruir/recriar sem afetar a máquina do usuário            |
| Prisma                       | Drizzle                       | Registrado em [[0002-stack-tecnologica]]                                                    |
| Vitest                       | Jest                          | Mais rápido, configuração mais simples com Vite/Next moderno, boa integração com TypeScript |
| Tailwind CSS para estilo     | CSS Modules puro              | Agilidade para montar o layout/dashboard rapidamente; decisão de baixo risco, não vira ADR  |

## Estrutura de pastas proposta

```
risch-financial-dashboard/
├── docs/                     # (já existe — SDD)
├── docker-compose.yml        # Postgres local
├── .env.example
├── prisma/
│   └── schema.prisma
├── src/
│   ├── app/
│   │   ├── layout.tsx        # layout raiz com sidebar/nav
│   │   ├── page.tsx          # redireciona ou landing simples
│   │   ├── renda-variavel/page.tsx
│   │   ├── renda-fixa/page.tsx
│   │   ├── gastos/page.tsx
│   │   └── api/health/route.ts
│   ├── components/
│   │   └── nav/
│   └── lib/
│       └── prisma.ts         # cliente Prisma singleton
├── package.json
├── tsconfig.json
├── .eslintrc / eslint.config
└── README.md                 # (já existe — será atualizado)
```

## Riscos e mitigação

- **Docker não instalado na máquina do usuário** → README documenta o
  pré-requisito e o comando de instalação; validar isso é a primeira task.
- **Prisma Client desatualizado em relação ao schema** → padronizar
  `npx prisma generate` como parte do script de dev/build.

## Estratégia de testes

- Casos críticos a cobrir: teste trivial garantindo que o setup de testes
  funciona (ex.: teste de um utilitário simples ou da rota de health check).
- Como validar manualmente: rodar `docker compose up`, depois o comando de
  dev, navegar pelas 3 seções no navegador, verificar que `/api/health`
  retorna sucesso.

## Plano de tasks

Ver [[001-setup-do-projeto (tasks)|docs/tasks/001-setup-do-projeto.md]] para a
quebra detalhada.
