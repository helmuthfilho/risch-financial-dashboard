---
name: novas-tasks
description: Quebra um plano técnico aprovado em tasks executáveis em docs/tasks/, seguindo o template do projeto, e — mediante autorização explícita do usuário — orquestra a implementação dessas tasks despachando clusters em paralelo para o agent executor-tasks, encadeando para a skill abrir-pull-request quando o usuário aprovar as mudanças. Use quando o usuário pedir para quebrar um plano em tasks, gerar a lista de tasks, avançar de plano para tasks no fluxo Spec → Plano → Tasks → Implementação, ou iniciar a execução de um arquivo de tasks já aprovado.
model: haiku
effort: medium
---

Ajuda a quebrar um plano técnico já existente em `docs/tasks/NNN-nome.md`,
seguindo `docs/sdd/workflow.md` e o template `docs/tasks/_template.md`. Ao
contrário das skills de spec/plano, essa etapa é mais mecânica — as decisões
já foram tomadas no plano; o trabalho aqui é sequenciar e dimensionar as
tasks direito. Além de gerar o arquivo de tasks, esta skill também cuida da
**execução**: uma vez autorizada, ela agrupa as tasks em clusters e despacha
cada cluster para o agent `executor-tasks` (`.claude/agents/executor-tasks.md`),
paralelizando o que puder. Ela não decide escopo de implementação — isso
continua vindo do plano.

Roda com `model: haiku` e `effort: medium`, e o agent `executor-tasks` que
ela despacha herda esse mesmo modelo (`model: inherit` no agent): tanto
quebrar o plano em tasks quanto executá-las é trabalho mecânico — as
decisões caras já foram tomadas em `nova-spec` (Opus) e `novo-plano`
(Sonnet).

Pode ser invocada automaticamente pela skill `novo-plano`, logo depois que o
usuário aprova um plano na mesma conversa (ver o Passo 4 de `novo-plano`).
Nesse caso, o plano-alvo já é conhecido — pule a pergunta de qual plano usar
e vá direto para o Passo 2 abaixo.

Todos os caminhos abaixo são relativos à raiz do repositório.

## Antes de começar

Leia (se ainda não estiverem no contexto desta conversa):

- O plano-alvo em `docs/plans/NNN-nome.md` — as tasks vêm diretamente das
  seções "Componentes afetados", "Modelo de dados" e "Estratégia de testes"
  dele.
- A spec correspondente em `docs/specs/NNN-nome.md`, para contexto do que
  cada task está construindo.
- `docs/sdd/constitution.md`, especialmente o princípio de testes
  ([[0004-testes-unitarios-obrigatorios-para-logica-de-negocio]]) — cada task
  que introduz lógica em `src/lib/**` inclui o teste unitário correspondente
  na mesma task, não numa task de "escrever testes" separada no final.
- Se existir uma skill `run-<projeto>` (`.claude/skills/run-*/SKILL.md`) com
  driver de navegador — a última task de validação manual referencia ela.
- `.claude/agents/executor-tasks.md` — o agent que executa cada cluster de
  tasks no Passo 5. Não precisa reescrevê-lo a cada vez; só o despache.

## Passo 1 — Localizar o plano e confirmar o número

Se não estiver claro qual plano, pergunte. Depois:

```bash
ls docs/plans/ | grep -E '^[0-9]{3}-' | sort
ls docs/tasks/ | grep -E '^[0-9]{3}-' | sort
```

O arquivo de tasks usa o **mesmo número e nome** do plano e da spec
(`docs/plans/002-x.md` → `docs/tasks/002-x.md`). Se o plano ainda está
`status: rascunho`, avise o usuário antes de prosseguir — não é bloqueante,
mas vale confirmar que ele quer quebrar em tasks algo ainda não aprovado.

## Passo 2 — Quebrar em tasks

Regras de granularidade e ordem (extraídas da prática já usada no projeto):

1. **Cada task cabe num diff só**, revisável isoladamente. Se uma task
   mistura duas responsabilidades sem relação direta (ex.: schema do banco +
   componente de UI), quebre em duas.
2. **Ordem de execução, de baixo pra cima**:
   - Schema do banco (Prisma) + migração, primeiro — todo o resto depende
     disso.
   - Utilitários e lógica pura de `src/lib/**` (validação, cálculos,
     conversões), **cada um com seu teste unitário na mesma task** — não
     separe "implementar" de "testar" em tasks diferentes.
   - Camada de acesso a dados / queries.
   - Camada de mutação (Server Actions, rotas de API — o que o plano tiver
     decidido).
   - UI, de componentes compartilhados para páginas específicas (ex.:
     formulário reutilizável antes das páginas que o usam).
   - Task final de verificação: rodar lint, testes (`npm run test:coverage`
     se houver lógica nova em `src/lib/**`), e build.
   - Task final de validação manual: usar o driver de navegador da skill
     `run-<projeto>` (se existir) para rodar o fluxo principal da feature
     ponta a ponta e conferir visualmente via screenshot; senão, descrever o
     roteiro de teste manual no navegador.
3. **Cada task referencia o(s) arquivo(s) exato(s)** que vai tocar (caminho
   completo), tirado das seções "Componentes afetados"/"Modelo de dados" do
   plano — não descrições vagas tipo "implementar backend". Isso não é só
   documentação: é o que permite decidir no Passo 5 quais tasks podem rodar
   em paralelo (arquivos disjuntos) e quais precisam ficar no mesmo cluster
   (arquivos compartilhados ou ordem explícita entre elas, ex.: "formulário
   reutilizável antes das páginas que o usam").
4. **Não invente escopo que não está no plano.** Se notar que falta algo no
   plano para a task fazer sentido, isso é sinal de voltar ao plano, não de
   decidir sozinho na hora de escrever as tasks.

## Passo 3 — Escrever o arquivo

Copie a estrutura de `docs/tasks/_template.md` para
`docs/tasks/NNN-slug-kebab-case.md` (mesmo slug do plano/spec), preenchendo:

- Frontmatter: `número`, `título` (mesmo do plano), `plano: docs/plans/NNN-nome.md`,
  `status: rascunho`, `criado_em`/`atualizado_em` com a data de hoje.
- Lista numerada de tasks, cada uma como checkbox (`- [ ] N. ...`), na ordem
  de execução do Passo 2.
- Seção "Notas de execução" vazia, com o placeholder do template — é
  preenchida durante a implementação, não agora.

## Passo 4 — Fechar o loop de planejamento

- Rode `npx prettier --write docs/tasks/NNN-*.md` para manter a formatação
  consistente com o resto do repo.
- Resuma para o usuário a lista de tasks e a ordem escolhida, e pergunte se
  quer ajustar algo antes de começar a implementação.
- **Não** dispare a execução automaticamente — ofereça como próximo passo
  (Passo 5) e só comece se o usuário autorizar explicitamente (ex.: "pode
  implementar", "começa a execução", "roda as tasks"). Aprovar a lista de
  tasks em si **não** é essa autorização — são dois "sim" diferentes, do
  mesmo jeito que aprovar a spec não implicava aprovar o plano.

## Passo 5 — Execução em clusters paralelos (só com autorização explícita)

Esta etapa só roda depois que o usuário autorizar a implementação (ver
Passo 4). Se ele só aprovou a lista de tasks, pare aí e espere.

### 5.1 — Montar as ondas e os clusters

Releia `docs/tasks/NNN-nome.md` e agrupe as tasks em **ondas**, na mesma
ordem de camadas do Passo 2 (schema → lib/utilitários → acesso a dados →
mutação → UI → verificação → validação manual). Ondas são sequenciais —
uma só começa depois que a anterior terminar inteira, porque cada camada
depende da anterior.

Dentro de cada onda, separe as tasks em **clusters**:

- Duas tasks só entram em clusters diferentes (paralelos) se tocam
  **arquivos disjuntos** e não há nenhuma ordem explícita entre elas no
  plano ou nas próprias tasks.
- Tasks que compartilham arquivo, ou que uma depende da outra ter sido
  feita antes (ex.: componente reutilizável antes da página que o usa),
  ficam no **mesmo cluster** — o `executor-tasks` as executa em sequência
  dentro desse cluster.
- Se uma onda tiver só uma task, ou todas as tasks da onda compartilharem
  arquivos, ela vira um único cluster — não force paralelismo onde não há.
- A task final de verificação (lint/testes/build) e a de validação manual
  nunca entram em paralelo com outra coisa: cada uma é sua própria onda,
  depois que todas as ondas de implementação terminarem.

### 5.2 — Despachar

Para cada onda, na ordem:

1. Dispare **um `Agent` (`subagent_type: executor-tasks`) por cluster da
   onda**, todos na mesma mensagem (chamadas paralelas) — nunca clusters de
   ondas diferentes na mesma leva. Cada dispatch leva: caminho de
   `docs/tasks/NNN-nome.md`, `docs/plans/NNN-nome.md` e
   `docs/specs/NNN-nome.md`; a lista exata de números de task do cluster; e
   os arquivos exclusivos daquele cluster.
2. Espere todos os clusters da onda retornarem antes de montar a próxima.
3. Releia `docs/tasks/NNN-nome.md` para confirmar que os checkboxes dos
   números despachados foram marcados e que "Notas de execução" foi
   atualizada.
4. Se algum cluster reportar bloqueio, conflito ou algo fora do plano,
   **pare a execução inteira**, resuma o bloqueio para o usuário e espere —
   não redistribua o cluster nem improvise sozinho.

### 5.3 — Verificação e validação manual

Depois que todas as ondas de implementação terminarem:

- Rode `npm run test:coverage` (se alguma task tocou `src/lib/**`), lint e
  build — pode ser você mesma ou um último dispatch de cluster dedicado a
  isso; reporte falhas ao usuário em vez de tentar corrigir sozinha sem
  avisar.
- Ofereça (não execute sozinha, a menos que o usuário já tenha pedido) a
  validação manual via driver de navegador da skill `run-<projeto>`, se
  existir.
- Nunca faça commit ou push a partir desta skill — isso fica para a skill
  `abrir-pull-request` (Passo 6), e só com autorização própria.

## Passo 6 — Abrir o Pull Request (aprovação separada, de novo)

Depois que o Passo 5.3 terminar e você tiver reportado o resultado da
verificação (lint/testes/build/validação manual) ao usuário, pergunte se
ele quer que o PR seja aberto — mostre um resumo curto do que mudou
(`git diff --stat`) junto com a pergunta.

Isso é um **terceiro "sim" distinto**, não o mesmo da lista de tasks
(Passo 4) nem o mesmo de autorizar a execução (Passo 5): aprovar a lista
não autoriza implementar, e implementar não autoriza abrir PR — abrir PR
empurra código pro GitHub, visível pra qualquer colaborador, então precisa
da própria aprovação explícita.

- **Se o usuário aprovar explicitamente** (ex.: "aprovado, abre o PR",
  "pode abrir o PR", "manda"): invoque a skill `abrir-pull-request`,
  passando o `NNN-nome` da feature como alvo — ela já sabe montar o corpo a
  partir de spec/plano/tasks e rodar o script que commita/pusha/abre o PR.
- **Se o usuário não aprovar** (ex.: "ainda não", "deixa eu revisar
  primeiro", ou simplesmente não comentar sobre o PR): **não** invoque
  `abrir-pull-request` — pare aqui, o trabalho de tasks está feito e as
  mudanças ficam no working tree local, sem commit, esperando o usuário.
