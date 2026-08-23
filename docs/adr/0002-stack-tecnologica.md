---
número: 0002
título: Stack tecnológica inicial
status: aceito
criado_em: 2026-08-22
---

# 0002 — Stack tecnológica inicial

## Status

Aceito

## Contexto

Precisamos escolher a base técnica para o dashboard financeiro pessoal antes
de iniciar o setup do projeto ([[001-setup-do-projeto]]). O usuário definiu,
em conversa direta, as seguintes preferências:

- Aplicação web rodando localmente (não app desktop nativo, não deploy em
  nuvem por enquanto — pode ser revisitado depois).
- Stack TypeScript full-stack.
- Banco de dados PostgreSQL.
- Entrada de dados priorizando importação de CSV/planilha (não cadastro
  manual como fluxo principal).

## Decisão

- **Framework**: Next.js (App Router) com TypeScript, cobrindo frontend e API
  no mesmo projeto.
- **Banco de dados**: PostgreSQL, rodando localmente via Docker Compose (sem
  precisar de instalação nativa do Postgres na máquina do usuário).
- **ORM**: Prisma. Motivo: boa integração com TypeScript (tipos gerados
  automaticamente), suporte nativo ao tipo `Decimal` do Postgres (`numeric`),
  o que é importante para o princípio "dinheiro nunca é float" ([[constitution]]
  item 1), e curva de aprendizado baixa para migrações de schema.
- **Execução**: apenas local (`localhost`) por enquanto. Hospedagem em nuvem
  fica para uma decisão futura, se e quando o usuário quiser acessar de fora
  de casa.

## Alternativas consideradas

- **Python (FastAPI) + React**: rejeitado por enquanto — dois ecossistemas
  separados aumentam a complexidade de setup para um projeto pessoal em fase
  inicial. Pode fazer sentido revisitar se cálculos financeiros complexos ou
  automações (scraping, jobs agendados) se tornarem um foco pesado.
- **Drizzle ORM** (em vez de Prisma): mais leve e com SQL mais explícito, mas
  ecossistema/tooling menos maduro para o caso de uso atual. Prisma prioriza
  velocidade de desenvolvimento inicial.
- **SQLite**: mais simples (sem precisar de Docker), mas o usuário optou por
  PostgreSQL explicitamente, considerando robustez a longo prazo.

## Consequências

- Requer Docker instalado na máquina do usuário para rodar o banco local.
- Um único ecossistema (Node/TypeScript) simplifica ferramentas de lint,
  testes e build.
- Migração futura para hospedagem em nuvem é direta, já que Next.js e
  PostgreSQL têm suporte amplo em provedores (Vercel + Postgres gerenciado,
  Railway, etc.), caso essa decisão mude.
