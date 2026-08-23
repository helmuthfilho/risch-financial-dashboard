# Dashboard Financeiro Pessoal

Aplicação para gerenciar portfólio financeiro pessoal: renda variável, renda
fixa e fluxo de caixa (cartão de crédito, PIX, gastos categorizados).

Este repositório segue um fluxo de **Spec-Driven Development (SDD)**: toda
funcionalidade não-trivial nasce como uma spec em `docs/specs/` antes de virar
código (ver `docs/sdd/workflow.md`).

## Rodando o projeto localmente

Pré-requisitos: [Node.js](https://nodejs.org) 20+ e [Docker](https://www.docker.com/).

```bash
# 1. instalar dependências
npm install

# 2. configurar variáveis de ambiente
cp .env.example .env

# 3. subir o PostgreSQL local
docker compose up -d

# 4. aplicar as migrações do banco
npx prisma migrate dev

# 5. rodar a aplicação em modo desenvolvimento
npm run dev
```

Acesse http://localhost:3000. A rota http://localhost:3000/api/health
confirma a conexão com o banco.

Outros comandos úteis:

```bash
npm run lint    # lint (ESLint)
npm run test    # testes (Vitest)
npm run build   # build de produção (também valida os tipos TypeScript)
```

## Como navegar

- `docs/sdd/constitution.md` — princípios não-negociáveis do projeto.
- `docs/sdd/glossary.md` — termos de domínio.
- `docs/sdd/workflow.md` — como o fluxo Spec → Plano → Tasks → Código funciona.
- `docs/specs/` — o quê e por quê de cada funcionalidade.
- `docs/plans/` — como cada spec será implementada.
- `docs/tasks/` — quebra de cada plano em passos executáveis.
- `docs/adr/` — decisões arquiteturais que atravessam mais de uma feature.

Ver `CLAUDE.md` para as regras que guiam como o assistente deve operar neste
repositório.
