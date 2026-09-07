---
name: novo-plano
description: Cria o plano técnico de uma spec aprovada em docs/plans/, entrevistando o usuário sobre as decisões técnicas e de negócio em aberto antes de escrever. Use quando o usuário pedir para planejar/detalhar tecnicamente uma spec, criar o plano técnico, ou avançar de spec para plano no fluxo Spec → Plano → Tasks.
model: sonnet
effort: medium
---

Ajuda a escrever o plano técnico (`docs/plans/NNN-nome.md`) de uma spec já
existente, seguindo `docs/sdd/workflow.md` e o template
`docs/plans/_template.md`. O que diferencia essa skill de só preencher o
template é a **entrevista**: antes de escrever qualquer coisa, ela levanta as
decisões técnicas que a spec deixou em aberto e pergunta ao usuário — em vez
de assumir silenciosamente. Esta skill só cuida do **plano** (o como) — não
escreve tasks nem implementa; isso fica para depois.

Divisão de responsabilidade com `nova-spec`, para não duplicar pergunta em
duas etapas: `nova-spec` entrevista e registra só os **requisitos
funcionais** (comportamento observável). Esta skill (`novo-plano`) parte
desses requisitos funcionais já prontos e é responsável por **planejar a
execução deles** e, adicionalmente, por **levantar os requisitos
não-funcionais** da feature (desempenho/volume, segurança/privacidade,
outros — ver a nova seção "Requisitos não-funcionais" de
`docs/plans/_template.md`). Por isso, toda pergunta feita nesta skill —
mesmo quando toca um caso de negócio como "o que mostrar antes de existir
dado" — existe para decidir um comportamento técnico a implementar, nunca
para renegociar escopo funcional (isso já foi fechado na spec).

Pode ser invocada automaticamente pela skill `nova-spec`, logo depois que o
usuário aprova uma spec na mesma conversa (ver o Passo 4 de `nova-spec`).
Nesse caso, a spec-alvo já é conhecida — pule a busca por qual spec usar no
Passo 1, garanta a branch dedicada no Passo 2 (isso roda sempre, mesmo
quando invocada automaticamente) e vá direto para a entrevista do Passo 3.

Roda com `model: sonnet` e `effort: medium`: já recebe a spec pronta como
insumo (o levantamento de contexto mais caro já foi feito por `nova-spec`,
em Opus), então essa etapa só precisa transformar decisões em plano técnico
— não precisa do modelo mais caro para isso.

Todos os caminhos abaixo são relativos à raiz do repositório.

## Antes de começar

Leia (se ainda não estiverem no contexto desta conversa):

- A spec-alvo em `docs/specs/NNN-nome.md` — o plano nasce dela, não pode
  contradizê-la.
- `docs/sdd/constitution.md` — princípios e convenções já travadas (ex.:
  dinheiro em centavos, testes unitários obrigatórios em `src/lib/**`).
- `docs/adr/` — decisões arquiteturais já tomadas em specs anteriores. Se uma
  decisão que este plano precisa tomar já foi resolvida por um ADR existente,
  **não pergunte de novo** — só aplique e referencie.
- `docs/plans/` (specs anteriores) — para manter consistência de padrões já
  estabelecidos (ex.: Server Actions vs. rotas `/api/`, convenções de nome).

## Passo 1 — Localizar a spec e confirmar o número

Se não estiver claro qual spec, pergunte. Depois:

```bash
ls docs/specs/ | grep -E '^[0-9]{3}-' | sort
ls docs/plans/ | grep -E '^[0-9]{3}-' | sort
```

O plano usa o **mesmo número e nome** da spec (`docs/specs/002-x.md` →
`docs/plans/002-x.md`). Se a spec ainda está `status: rascunho`, avise o
usuário antes de prosseguir — não é bloqueante, mas vale confirmar que ele
quer planejar algo ainda não aprovado.

## Passo 2 — Garantir uma branch dedicada

Antes de entrevistar o usuário ou escrever qualquer coisa, garanta que este
plano — e as tasks/implementação que vêm depois dele — não caem direto na
branch principal.

```bash
git branch --show-current
git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@'
```

O segundo comando dá o nome real da branch principal do repositório remoto
(normalmente `main`, mas não assuma — use o que ele retornar; se não
retornar nada, caia para `main`).

- **Já está numa branch diferente da principal**: nada a fazer, continue
  nela — presuma que já foi criada para este trabalho.
- **Está na branch principal**: antes de criar a nova branch, rode
  `git status`. Se houver mudanças não commitadas que não sejam a spec
  deste tema (ex.: arquivos de outra funcionalidade em andamento que
  alguém esqueceu de commitar), **pare e avise o usuário** em vez de levar
  tudo para a nova branch sem avisar — não é destrutivo (`checkout -b` não
  descarta nada), mas pode misturar trabalhos diferentes.
  Depois, crie a branch **a partir da branch principal** e mude para ela:

  ```bash
  git checkout -b feat/<slug> <branch-principal>
  ```

  `<slug>` é o mesmo slug kebab-case do arquivo da spec
  (`docs/specs/NNN-<slug>.md`, sem o `NNN-`) — o nome já descreve a
  funcionalidade, reaproveite-o em vez de inventar outro. Isso segue o
  padrão já usado no repositório (`feat/redesign-visual-home`,
  `feat/sdd-setup-e-renda-fixa`).

- **Já existe uma branch com esse nome** (ex.: retomando um plano
  interrompido): troque para ela (`git checkout feat/<slug>`) em vez de
  tentar recriá-la.
- Depois de trocar, avise o usuário em uma frase qual branch está sendo
  usada (nova ou já existente). Não é preciso pedir aprovação para isso —
  é uma ação local e reversível — mas o usuário precisa saber onde o
  trabalho está pousando.

## Passo 3 — A entrevista

Releia a spec inteira (requisitos funcionais, critérios de aceite, desvios
da constituição, perguntas em aberto) e monte uma lista de decisões técnicas
necessárias para implementá-la — incluindo os requisitos não-funcionais, que
são responsabilidade desta skill, não da spec. Categorias comuns a
verificar:

- **Modelo de dados**: novas tabelas/campos, o que fica armazenado vs. o que
  é calculado em tempo de leitura, chaves, relações, o que é histórico vs.
  estado atual.
- **Onde a lógica mora**: Server Action, rota `/api/`, ou outro padrão — veja
  se specs anteriores já estabeleceram um padrão (ex.: `docs/plans/002-*`
  usou Server Actions) antes de reabrir essa decisão do zero.
- **Bibliotecas novas**: validação, parsing, cálculo, formatação — qual usar
  e por quê, alternativas descartadas.
- **Volume de dados / performance**: qual escala é esperada (linhas, chamadas,
  frequência)? Isso muda a escolha entre calcular em tempo de leitura vs.
  armazenar/cachear? Vira o item "Desempenho / volume de dados esperado" da
  seção "Requisitos não-funcionais" do plano.
- **Segurança / privacidade**: algum dado novo sensível entrando no sistema
  (considerando sempre "dados financeiros são sensíveis por padrão")? Como
  ele é tratado (log, exibição, exportação)? Vira o item "Segurança /
  privacidade" da mesma seção do plano.
- **Estratégia de testes**: quais casos críticos de `src/lib/**` precisam de
  teste unitário (lembrando do coverage mínimo de 80%, [[0004-testes-unitarios-obrigatorios-para-logica-de-negocio]]);
  o que só dá pra validar via navegador.
- **Casos-limite de negócio**: comportamento esperado quando um dado
  obrigatório para o cálculo/exibição ainda não existe (ex.: "o que mostrar
  como valor atual antes de qualquer atualização?" — isso é uma decisão de
  produto com implicação técnica direta).

Para cada decisão, classifique:

1. **Baixo risco / já coberta por convenção do projeto** (stack definida em
   ADR, padrão repetido em specs anteriores, escolha sem trade-off real) →
   decida você mesmo e registre com alternativas consideradas na tabela
   "Decisões técnicas" do plano. Não precisa perguntar.
2. **Consequente / com trade-off real ou efeito fora dessa feature** →
   pergunte ao usuário com a ferramenta de pergunta (`AskUserQuestion`),
   agrupando perguntas relacionadas numa única chamada (até 4 perguntas),
   com opções claras e uma marcada como "(Recomendado)" quando você tiver
   uma opinião. Perguntas podem ser técnicas (ex.: "cachear esse valor ou
   calcular em tempo real?") ou de negócio (ex.: "o que fazer nesse caso
   limite?") — o que importa é que a resposta muda o desenho do plano.

Se, durante a entrevista, uma resposta revelar uma decisão que **atravessa
mais do que essa feature** (vai se repetir em Renda Variável/Gastos/outras
áreas), pergunte ao usuário se ele quer formalizar isso como um ADR em
`docs/adr/` além do plano — foi o que aconteceu com
[[0003-dinheiro-como-inteiro-em-centavos]] e
[[0004-testes-unitarios-obrigatorios-para-logica-de-negocio]]. Não crie o ADR
sem essa confirmação, mas também não deixe uma decisão claramente
cross-cutting enterrada só no plano.

## Passo 4 — Escrever o plano

Copie a estrutura de `docs/plans/_template.md` para
`docs/plans/NNN-slug-kebab-case.md` (mesmo slug da spec), preenchendo:

- Frontmatter: `número`, `título` (mesmo da spec), `spec: docs/specs/NNN-nome.md`,
  `status: rascunho`, `criado_em`/`atualizado_em` com a data de hoje.
- **Visão geral**: 2-3 frases de como a spec será implementada.
- **Componentes afetados**: frontend, backend, banco de dados, outros.
- **Modelo de dados**: schema novo/alterado. Sempre respeitando
  [[constitution]] (dinheiro em centavos, nomenclatura em inglês para
  código).
- **Requisitos não-funcionais**: desempenho/volume esperado, segurança e
  privacidade, outros — preenchido a partir das respostas da entrevista
  (Passo 3), nunca copiado da spec (ela não tem mais essa seção).
- **Decisões técnicas**: tabela com decisão, alternativas consideradas,
  motivo — tanto as que você decidiu sozinho quanto as respondidas na
  entrevista. Se alguma virou ADR, referencie-o aqui em vez de repetir o
  raciocínio.
- **Riscos e mitigação**: riscos reais levantados na entrevista (ex.:
  serialização de tipos exóticos entre server/client, escala de uma query),
  não riscos genéricos de preencher espaço.
- **Estratégia de testes**: casos críticos de `src/lib/**` a cobrir e como
  validar manualmente (via a skill `run-<projeto>` de navegador, se existir).
- **Plano de tasks**: aponta para `docs/tasks/NNN-nome.md` ("a criar").

## Passo 5 — Fechar o loop

- Rode `npx prettier --write docs/plans/NNN-*.md` (e qualquer ADR novo) para
  manter a formatação consistente com o resto do repo.
- Se algum ADR novo foi criado no Passo 3, atualize `docs/sdd/constitution.md`
  quando a decisão for realmente um princípio do projeto (bump de versão),
  do jeito que [[0003-dinheiro-como-inteiro-em-centavos]] e
  [[0004-testes-unitarios-obrigatorios-para-logica-de-negocio]] fizeram.
- Resuma para o usuário as decisões tomadas (respondidas por ele vs.
  decididas por você) e pergunte se quer aprovar o plano.
- **Quando o usuário aprovar o plano** nesta mesma conversa (ex.: "aprovado",
  "pode seguir", "tá bom"): atualize `status: aprovado` no frontmatter e, em
  seguida, **invoque a skill `novas-tasks` automaticamente**, sem esperar um
  pedido separado — passe o plano recém-aprovado como alvo, para ela não
  perguntar de novo qual plano usar. Isso é seguro porque gerar o arquivo de
  tasks não implementa nada sozinho: `novas-tasks` só despacha a execução em
  clusters depois de uma autorização explícita e separada do usuário, além
  da aprovação da lista de tasks em si.
- Se o usuário não sinalizar aprovação (ex.: "vou revisar depois", ou
  simplesmente não comentar), **não** avance sozinho — só ofereça o próximo
  passo e espere.
- **Não** implemente código a partir desta skill em nenhuma circunstância —
  isso é sempre gate de `novas-tasks`/da implementação em si, nunca daqui.
