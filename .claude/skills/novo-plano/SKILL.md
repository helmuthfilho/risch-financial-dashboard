---
name: novo-plano
description: Cria o plano técnico de uma spec aprovada em docs/plans/, entrevistando o usuário sobre as decisões técnicas e de negócio em aberto antes de escrever. Use quando o usuário pedir para planejar/detalhar tecnicamente uma spec, criar o plano técnico, ou avançar de spec para plano no fluxo Spec → Plano → Tasks.
---

Ajuda a escrever o plano técnico (`docs/plans/NNN-nome.md`) de uma spec já
existente, seguindo `docs/sdd/workflow.md` e o template
`docs/plans/_template.md`. O que diferencia essa skill de só preencher o
template é a **entrevista**: antes de escrever qualquer coisa, ela levanta as
decisões técnicas e de negócio que a spec deixou em aberto e pergunta ao
usuário — em vez de assumir silenciosamente. Esta skill só cuida do **plano**
(o como) — não escreve tasks nem implementa; isso fica para depois.

Pode ser invocada automaticamente pela skill `nova-spec`, logo depois que o
usuário aprova uma spec na mesma conversa (ver o Passo 4 de `nova-spec`).
Nesse caso, a spec-alvo já é conhecida — pule a busca por qual spec usar no
Passo 1 e vá direto para a entrevista do Passo 2.

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

## Passo 2 — A entrevista

Releia a spec inteira (requisitos funcionais, não-funcionais, critérios de
aceite, desvios da constituição, perguntas em aberto) e monte uma lista de
decisões técnicas necessárias para implementá-la. Categorias comuns a
verificar:

- **Modelo de dados**: novas tabelas/campos, o que fica armazenado vs. o que
  é calculado em tempo de leitura, chaves, relações, o que é histórico vs.
  estado atual.
- **Onde a lógica mora**: Server Action, rota `/api/`, ou outro padrão — veja
  se specs anteriores já estabeleceram um padrão (ex.: `docs/plans/002-*`
  usou Server Actions) antes de reabrir essa decisão do zero.
- **Bibliotecas novas**: validação, parsing, cálculo, formatação — qual usar
  e por quê, alternativas descartadas.
- **Volume de dados / performance**: a spec já definiu isso na seção de
  requisitos não-funcionais? Se não, é uma pergunta de negócio, não técnica.
- **Segurança / privacidade**: algum dado novo sensível entrando no sistema?
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

## Passo 3 — Escrever o plano

Copie a estrutura de `docs/plans/_template.md` para
`docs/plans/NNN-slug-kebab-case.md` (mesmo slug da spec), preenchendo:

- Frontmatter: `número`, `título` (mesmo da spec), `spec: docs/specs/NNN-nome.md`,
  `status: rascunho`, `criado_em`/`atualizado_em` com a data de hoje.
- **Visão geral**: 2-3 frases de como a spec será implementada.
- **Componentes afetados**: frontend, backend, banco de dados, outros.
- **Modelo de dados**: schema novo/alterado. Sempre respeitando
  [[constitution]] (dinheiro em centavos, nomenclatura em inglês para
  código).
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

## Passo 4 — Fechar o loop

- Rode `npx prettier --write docs/plans/NNN-*.md` (e qualquer ADR novo) para
  manter a formatação consistente com o resto do repo.
- Se algum ADR novo foi criado no Passo 2, atualize `docs/sdd/constitution.md`
  quando a decisão for realmente um princípio do projeto (bump de versão),
  do jeito que [[0003-dinheiro-como-inteiro-em-centavos]] e
  [[0004-testes-unitarios-obrigatorios-para-logica-de-negocio]] fizeram.
- Resuma para o usuário as decisões tomadas (respondidas por ele vs.
  decididas por você) e pergunte se quer aprovar o plano.
- **Quando o usuário aprovar o plano** nesta mesma conversa (ex.: "aprovado",
  "pode seguir", "tá bom"): atualize `status: aprovado` no frontmatter e, em
  seguida, **invoque a skill `novas-tasks` automaticamente**, sem esperar um
  pedido separado — passe o plano recém-aprovado como alvo, para ela não
  perguntar de novo qual plano usar. Isso é seguro porque `novas-tasks` só
  gera o arquivo de tasks; ela mesma não implementa sem autorização explícita
  do usuário.
- Se o usuário não sinalizar aprovação (ex.: "vou revisar depois", ou
  simplesmente não comentar), **não** avance sozinho — só ofereça o próximo
  passo e espere.
- **Não** implemente código a partir desta skill em nenhuma circunstância —
  isso é sempre gate de `novas-tasks`/da implementação em si, nunca daqui.
