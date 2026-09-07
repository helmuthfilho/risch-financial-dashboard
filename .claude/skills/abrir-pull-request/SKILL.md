---
name: abrir-pull-request
description: Abre um Pull Request no GitHub para uma feature já implementada pelo fluxo de Spec-Driven Development do projeto (spec → plano → tasks → implementação), seguindo o template padrão de descrição de PR do repo. Use quando a skill novas-tasks terminar de executar/verificar um cluster de tasks e o usuário aprovar explicitamente as mudanças feitas, ou quando o usuário pedir diretamente para abrir/criar um PR de uma feature já implementada via SDD.
model: haiku
effort: low
---

Abre o PR de uma feature que passou pelo fluxo SDD do projeto
(`docs/sdd/workflow.md`): spec aprovada, plano aprovado, tasks executadas.
Não escreve código, não decide o que entra no PR além do que já foi
implementado e aprovado, não faz merge, nunca força push.

Roda com `model: haiku` e `effort: low`: o trabalho aqui é extrair conteúdo
já escrito em `docs/specs|plans|tasks/NNN-nome.md` (spec = o quê, plano =
como e por quê, tasks = notas de execução com o que foi feito) e montar o
corpo do PR a partir disso — pouca síntese nova, quase só recombinar texto
que já existe. A parte que exigiria comandos repetitivos e propensos a erro
(branch, commit, push, `gh pr create`) fica no script
`scripts/abrir_pr.py`, não em raciocínio do modelo.

## O gate de aprovação — antes de qualquer outra coisa

Esta skill **nunca** roda o script sem uma aprovação explícita e separada
do usuário, nesta mesma conversa, para abrir o PR com as mudanças atuais —
isso não é o mesmo "sim" de aprovar a lista de tasks nem o mesmo "sim" de
autorizar a execução (ver Passo 4 e Passo 5 de `novas-tasks`). São gates
diferentes porque abrir um PR empurra código para o GitHub, visível para
qualquer colaborador — é uma ação de blast radius maior que escrever um
arquivo local.

- Se esta skill foi invocada automaticamente pela skill `novas-tasks` **e**
  a mensagem do usuário que disparou essa invocação já continha a
  aprovação explícita das mudanças (ex.: "aprovado, pode abrir o PR",
  "tá bom, abre o PR"), prossiga.
- Se foi invocada sem essa aprovação explícita já presente na conversa —
  seja porque o usuário só aprovou a lista de tasks/a execução, seja porque
  foi chamada diretamente — **pare**, mostre um resumo do que mudaria
  (`git status --short` e `git diff --stat`) e pergunte explicitamente se
  pode abrir o PR. Só continue com um "sim" real.

## Passo 1 — Confirmar o alvo

Descubra `NNN-nome` (o mesmo número/slug usado em spec, plano e tasks). Se
não estiver claro pelo contexto da conversa, infira pela branch atual
(convenção `feat/<slug>` de `novo-plano`) cruzando com:

```bash
git branch --show-current
ls docs/tasks/ | grep -E '^[0-9]{3}-'
```

Confirme que os três arquivos existem e estão em ordem:

- `docs/specs/NNN-nome.md` — idealmente `status: aprovado`.
- `docs/plans/NNN-nome.md` — idealmente `status: aprovado`.
- `docs/tasks/NNN-nome.md` — as tasks relevantes marcadas `- [x]`. Se
  alguma tarefa relevante ainda não foi marcada, avise o usuário antes de
  seguir (pode ser intencional, um PR parcial — mas não assuma).

Se qualquer um faltar ou o número não ficar claro, pergunte em vez de
adivinhar.

## Passo 2 — Montar o corpo do PR

Copie a estrutura de `assets/pr_template.md` (ela documenta, em
comentários HTML, de onde tirar cada seção) para um arquivo temporário e
preencha:

- **Resumo**: 2-4 frases a partir de "Objetivo"/"Contexto e motivação" da
  spec, com os links para os três documentos.
- **O que mudou**: a partir de "Notas de execução" de `docs/tasks/NNN-nome.md`
  (cada task já registrou o que fez e quais arquivos tocou) — cruze com
  `git diff --stat <branch-base>...HEAD` pra garantir que nada ficou de
  fora.
- **Por que essas decisões**: a partir da tabela "Decisões técnicas" e de
  "Riscos e mitigação" do plano. Só as decisões não-óbvias — não repita
  decisões triviais.
- **Test plan**: checklist do que **de fato** rodou e passou nesta sessão
  (lint, `npm run test:coverage`, build, validação manual via
  `run-<projeto>` se existir) — nunca marque `- [x]` para algo que não foi
  confirmado; se algo ficou pendente, marque `- [ ]` e diga por quê.
- **Notas / follow-ups conhecidos**: opcional, só se houver desvio real do
  plano ou limitação conhecida. Remova a seção se não houver nada.
- Rodapé: links para spec/plano/tasks e a atribuição de PR **vigente nesta
  sessão** (a instrução de atribuição do ambiente atual, nunca um valor
  fixo copiado de um exemplo antigo — isso muda por sessão/modelo).

## Passo 3 — Escolher o título

Convenção já usada no repo (ver `git log`): `feat: <resumo curto>` para
funcionalidade nova, `fix:` só se o PR for estritamente uma correção,
`refactor:` se for só reestruturação sem mudar comportamento. Curto,
imperativo, sem ponto final.

## Passo 4 — Rodar o script

```bash
python3 .claude/skills/abrir-pull-request/scripts/abrir_pr.py \
  --title "feat: <resumo curto>" \
  --body-file <caminho do corpo montado no Passo 2> \
  [--commit-message "<mesma linha do título, se houver mudança não commitada>"] \
  [--draft]
```

Não passe `--base`/`--head` a menos que precise sobrescrever a detecção
automática (branch principal via `origin/HEAD`, branch atual via `git
branch --show-current`). O script recusa abrir PR de uma branch para ela
mesma e nunca commita sem `--commit-message` explícito — se ele parar
pedindo uma mensagem de commit, forneça uma curta e específica, não
genérica tipo "mudanças".

Use `--dry-run` primeiro se quiser conferir os comandos antes de
efetivamente commitar/pushar/criar o PR.

## Passo 5 — Reportar

Devolva ao usuário a URL do PR que o script imprimir. Se o script falhar
(branch errada, `gh` não autenticado, PR já existe para essa branch,
conflito ao commitar), mostre a mensagem de erro exata e pare — não tente
"consertar" sozinha por conta própria (ex.: não force push, não recrie a
branch, não pule a checagem de aprovação numa segunda tentativa).

Nunca faça merge do PR a partir desta skill — abrir é o único trabalho
dela; o merge é decisão do usuário (ou de quem revisar) no GitHub.
