---
name: nova-spec
description: Cria uma nova spec de funcionalidade em docs/specs/, seguindo o fluxo de Spec-Driven Development do projeto (docs/sdd/workflow.md). Use quando o usuário pedir para criar/escrever/especificar uma nova funcionalidade, iniciar uma spec, ou começar o fluxo Spec → Plano → Tasks para algo novo.
model: opus
effort: high
---

Ajuda a escrever uma nova spec de funcionalidade para o dashboard financeiro,
seguindo `docs/sdd/workflow.md` e o template `docs/specs/_template.md`. Esta
skill só cuida da **spec** (o quê / por quê) — não escreve o plano técnico
nem as tasks; isso fica para depois, com o próprio fluxo do projeto ou com
uma spec futura dedicada a isso.

Escopo estrito: esta skill entrevista e registra só os **requisitos
funcionais** (o comportamento observável da feature). Não pergunte sobre
desempenho, volume de dados, segurança/privacidade técnica ou qualquer
outro requisito não-funcional — isso é levantado depois, na entrevista
puramente técnica da skill `novo-plano`, para não duplicar pergunta sobre o
mesmo assunto em duas etapas. Se o usuário trouxer voluntariamente um
requisito não-funcional durante esta conversa, anote-o mentalmente e avise
que ele será formalizado no plano, em vez de criar uma seção pra isso na
spec.

Roda com `model: opus` e `effort: high` de propósito: é a etapa que reúne o
máximo de contexto do repositório (constituição, glossário, specs/ADRs
anteriores) e toma as decisões de escopo mais caras de errar — vale gastar
mais tokens aqui para que `novo-plano` e `novas-tasks`, mais adiante, possam
rodar com modelos mais baratos em cima de uma spec já bem fundamentada.

Todos os caminhos abaixo são relativos à raiz do repositório.

## Antes de começar

Leia (se ainda não estiverem no contexto desta conversa):

- `docs/sdd/constitution.md` — princípios não-negociáveis que a spec precisa
  respeitar ou justificar desvio.
- `docs/sdd/glossary.md` — termos de domínio já definidos.
- `docs/sdd/workflow.md` — regras de quando uma spec é necessária vs. quando
  se pode pular direto para código.

## Passo 1 — Determinar o número da spec

```bash
ls docs/specs/ | grep -E '^[0-9]{3}-' | sort
```

Pegue o maior `NNN` existente e use `NNN + 1`, com 3 dígitos
(`001`, `002`, ..., `010`). Esse número será compartilhado entre a spec, o
plano e as tasks do mesmo tema (`docs/specs/NNN-nome.md`,
`docs/plans/NNN-nome.md`, `docs/tasks/NNN-nome.md`).

## Passo 2 — Reunir o conteúdo

Converse com o usuário (ou use o que já foi dito na conversa) para preencher
cada seção do template. **Não pergunte o que já é óbvio pelo contexto** — só
pergunte o que for genuinamente indefinido. Itens a esclarecer:

- **Título** curto da funcionalidade (vira o slug do arquivo, kebab-case,
  ex.: "Importação de Fatura de Cartão" → `importacao-fatura-cartao`).
- **Contexto e motivação**: por que essa feature existe, que problema real
  resolve.
- **Objetivo**: uma frase clara do resultado desejado.
- **Escopo**: o que entra e o que fica de fora explicitamente. Verificar se
  algo do "fora de escopo" da própria spec já está coberto pela seção 3 da
  constituição (`docs/sdd/constitution.md`) — se estiver, basta referenciar,
  não repetir.
- **Requisitos funcionais**: lista numerada, comportamento observável. Esta
  é a seção central da spec — insista aqui até cobrir todo o comportamento
  esperado, mesmo que isso signifique várias rodadas de pergunta.
- **Critérios de aceite**: checklist verificável, não ambíguo — derivado dos
  requisitos funcionais, não de requisitos técnicos/não-funcionais (esses
  ficam para os critérios de aceite do plano, se fizer sentido lá).
- **Desvios da constituição**: avalie contra os 7 princípios de
  `docs/sdd/constitution.md`. Se não houver tensão, escreva "nenhum" — não
  pule essa seção.
- **Perguntas em aberto**: dúvidas reais que ainda não têm resposta. Tudo
  bem deixar itens aqui; a spec não precisa estar 100% fechada para virar
  `rascunho`.

Se o assunto trouxer termos de domínio novos (ex.: um tipo de ativo ou
evento financeiro ainda não listado), adicione-os a
`docs/sdd/glossary.md` em ordem alfabética como parte do mesmo trabalho.

## Passo 3 — Escrever o arquivo

Copie a estrutura de `docs/specs/_template.md` para
`docs/specs/NNN-slug-kebab-case.md`, preenchendo:

- Frontmatter: `número` (sem zero-padding no campo, ex. `7`, mas o arquivo
  usa `007`), `título`, `status: rascunho`, `criado_em` e `atualizado_em`
  com a data de hoje (formato `AAAA-MM-DD`).
- Todas as seções do corpo, na mesma ordem do template.
- Use `[[constitution]]`, `[[glossary]]`, `[[workflow]]` para referenciar os
  outros documentos, do mesmo jeito que a spec `001` já faz.

## Passo 4 — Fechar o loop

- Rode `npx prettier --write docs/specs/NNN-*.md` (e o glossário, se
  editado) para manter a formatação consistente com o resto do repo.
- Resuma para o usuário o que foi escrito e pergunte se o conteúdo reflete
  a intenção dele — specs não precisam de aprovação formal aqui, mas o
  usuário deve revisar antes de considerá-la `aprovada`.
- **Quando o usuário aprovar a spec** nesta mesma conversa (ex.: "aprovado",
  "pode seguir", "tá bom"): atualize `status: aprovado` no frontmatter e, em
  seguida, **invoque a skill `novo-plano` automaticamente**, sem esperar um
  pedido separado — passe a spec recém-aprovada como alvo, para ela não
  perguntar de novo qual spec usar. `novo-plano` só entrevista o usuário e
  escreve o plano; ela mesma encadeia para `novas-tasks` só depois de o
  plano ser aprovado, e nada disso chega a implementar código sem
  autorização explícita.
- Se o usuário não sinalizar aprovação (ex.: "vou revisar depois", ou
  simplesmente não comentar), **não** avance sozinho — só ofereça o próximo
  passo e espere.
- Se a spec tensiona algo fora do escopo atual da constituição (ex.: pede
  multi-usuário ou integração bancária automática), avise explicitamente
  antes de escrever, já que isso é uma mudança de princípio, não só de
  feature.
