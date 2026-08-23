---
número: 001
título: Setup do Projeto
status: concluído
criado_em: 2026-08-22
atualizado_em: 2026-08-22
---

# 001 — Setup do Projeto

## Contexto e motivação

Antes de qualquer funcionalidade de domínio (renda variável, renda fixa,
gastos), precisamos de um esqueleto de aplicação rodando localmente: projeto
inicializado, banco de dados conectado, navegação básica entre as três áreas
do dashboard, e ferramentas de qualidade (lint, testes) configuradas. Sem
isso, nenhuma spec de feature tem onde "pousar".

## Objetivo

Ter uma aplicação web rodando em `localhost`, com navegação entre as três
áreas do dashboard (Renda Variável, Renda Fixa, Gastos), conectada a um banco
PostgreSQL local, pronta para receber as próximas specs de domínio.

## Escopo

### Dentro do escopo

- Inicialização do projeto Next.js + TypeScript.
- Banco de dados PostgreSQL rodando localmente via Docker Compose.
- Camada de acesso a dados configurada (ORM) e conectada ao banco.
- Layout base da aplicação com navegação entre 3 seções: Renda Variável,
  Renda Fixa, Gastos (cada uma como uma página placeholder por enquanto).
- Lint, formatação e execução de testes configurados e funcionando.
- Documentação de como rodar o projeto localmente (README).

### Fora do escopo

- Qualquer funcionalidade real de domínio (cadastro de ativos, importação de
  CSV, cálculo de posições, categorização de gastos) — isso será objeto de
  specs futuras (`002-...`, `003-...`).
- Autenticação (aplicação é single-user local, ver [[constitution]] item 4).
- Deploy em nuvem.

## Requisitos funcionais

1. Ao rodar o comando de desenvolvimento, a aplicação sobe em `localhost` e é
   acessível pelo navegador.
2. A aplicação tem uma navegação (menu/sidebar) com 3 itens: Renda Variável,
   Renda Fixa, Gastos. Cada um leva a uma página própria (mesmo que vazia por
   enquanto).
3. A aplicação consegue se conectar ao banco PostgreSQL local e executar uma
   query trivial de verificação (ex.: uma página de status/health check).
4. Existe um comando único para subir o banco de dados local (Docker Compose).
5. Existe um comando único para rodar lint e um comando único para rodar
   testes.

## Requisitos não-funcionais

- Desempenho / volume de dados esperado: irrelevante nesta etapa (sem dados
  reais ainda).
- Segurança / privacidade (ver [[constitution]] item 2): credenciais de banco
  ficam em `.env` (não versionado); `.env.example` documenta as variáveis
  necessárias sem valores reais.
- Reprodutibilidade: qualquer pessoa (ou o próprio usuário em outra máquina)
  deve conseguir clonar o repositório e rodar a aplicação seguindo apenas o
  README.

## Critérios de aceite

- [x] `docker compose up` sobe um Postgres local funcional.
- [x] Comando de dev sobe a aplicação Next.js sem erros.
- [x] Navegação entre as 3 seções funciona no navegador.
- [x] Uma página/rota simples confirma conexão bem-sucedida com o banco.
- [x] Comando de lint roda sem erros no código gerado pelo setup.
- [x] Comando de testes roda (mesmo que com um teste trivial) sem erros.
- [x] README explica como rodar o projeto do zero.

## Desvios da constituição

Nenhum.

## Perguntas em aberto

- Nenhuma no momento — decisões de stack (Next.js + TypeScript, PostgreSQL,
  execução local) já definidas com o usuário; detalhes técnicos (ORM,
  ferramentas de lint/teste específicas) ficam no plano.
