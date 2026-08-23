---
número: 001
título: Setup do Projeto
plano: docs/plans/001-setup-do-projeto.md
status: concluído
criado_em: 2026-08-22
atualizado_em: 2026-08-22
---

# 001 — Tasks: Setup do Projeto

- [x] 1. Inicializar o projeto Next.js + TypeScript (App Router) na raiz do
      repositório, preservando `docs/`, `CLAUDE.md` e `README.md` existentes.
- [x] 2. Configurar ESLint + Prettier e garantir que `npm run lint` passa.
- [x] 3. Configurar Vitest e adicionar um teste trivial; garantir que
      `npm run test` passa.
- [x] 4. Criar `docker-compose.yml` com serviço PostgreSQL local; criar
      `.env.example` com as variáveis necessárias (`DATABASE_URL` etc.).
- [x] 5. Instalar e configurar Prisma; criar `prisma/schema.prisma` inicial
      (datasource + generator, sem tabelas de domínio); rodar a primeira
      migração vazia contra o Postgres local.
- [x] 6. Criar cliente Prisma singleton em `src/lib/prisma.ts`.
- [x] 7. Criar rota `/api/health` que executa uma query trivial no banco e
      retorna status de sucesso/erro.
- [x] 8. Criar layout base (`src/app/layout.tsx`) com navegação (sidebar ou
      topbar) contendo os 3 itens: Renda Variável, Renda Fixa, Gastos.
- [x] 9. Criar as 3 páginas placeholder (`/renda-variavel`, `/renda-fixa`,
      `/gastos`) com conteúdo mínimo indicando "em construção".
- [x] 10. Atualizar `README.md` com instruções completas de setup: pré-requisitos
      (Node, Docker), como subir o banco, como rodar a aplicação, como rodar
      lint/testes.
- [x] 11. Atualizar a seção "Stack" do `CLAUDE.md` com a stack definitiva.
- [x] 12. Validação manual: subir banco + app, navegar pelas 3 seções,
      confirmar `/api/health` OK, rodar lint e testes uma última vez.

## Notas de execução

- `create-next-app` não permite rodar direto num diretório com arquivos
  existentes (`CLAUDE.md`, `README.md`); o projeto foi gerado num diretório
  temporário e mesclado na raiz, preservando `docs/`, `.git/`, `README.md` e
  `CLAUDE.md` originais.
- O Next.js/`create-next-app` mais recente gera um `AGENTS.md` (regras de
  agente específicas do Next, regeneradas por `next dev`) e um `CLAUDE.md`
  próprio (`@AGENTS.md`). Resolvido mesclando: mantido o `CLAUDE.md` do SDD e
  adicionada a linha `@AGENTS.md` no final para importar as regras do Next.
- `vitest.config.ts` como CommonJS falhava com `ERR_REQUIRE_ESM` (dependência
  `std-env` é ESM-only); resolvido renomeando para `vitest.config.mts`.
- Rodado `npm run build` (não só `tsc --noEmit`) para validar tipos, pois o
  tipo `LayoutProps` do App Router só existe nos tipos gerados por
  `next dev`/`next build`.
- `npm audit` reporta 3 vulnerabilidades "high" em `deepmerge-ts` (dependência
  transitiva do `@prisma/config`, usada só pela CLI do Prisma em dev — risco
  de exaustão de pilha ao processar configs profundamente aninhadas, não
  exposto em runtime). Fix disponível apenas via downgrade do Prisma
  (`npm audit fix --force`); deixado como está por ora, revisar quando o
  Prisma lançar uma versão corrigida.
