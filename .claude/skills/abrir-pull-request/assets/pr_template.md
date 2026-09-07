<!--
Template de descrição de PR para features implementadas pelo fluxo SDD do
projeto (spec → plano → tasks → implementação). A skill abrir-pull-request
preenche cada seção usando o que já foi escrito nesses documentos — isso
não é um formulário em branco para o usuário preencher depois, é o que a
skill deve entregar pronto.

Todo PR aberto por essa skill segue esta estrutura, na mesma ordem. Remova
uma seção só se genuinamente não houver conteúdo para ela (ex.: "Notas /
follow-ups conhecidos" quando nada saiu do previsto no plano) — nunca deixe
uma seção com um placeholder vazio ou genérico tipo "N/A" sem explicação.
-->

## Resumo

<!--
2-4 frases: o que essa feature faz e por quê, no nível de negócio (não de
implementação). Puxe de "Objetivo" e "Contexto e motivação" da spec. Inclua
os links para spec/plano/tasks (docs/specs/NNN-nome.md, docs/plans/NNN-nome.md,
docs/tasks/NNN-nome.md) logo no início desta seção.
-->

## O que mudou

<!--
Lista do que foi implementado, arquivo por arquivo ou área por área — puxe
das "Notas de execução" de docs/tasks/NNN-nome.md (cada task já registrou o
que fez e quais arquivos tocou) e cruze com `git diff --stat` para garantir
que nada ficou de fora. Isso é "como foi implementado" na prática: o que
existe agora que não existia antes.
-->

## Por que essas decisões

<!--
As decisões técnicas não-óbvias e o motivo — puxe da tabela "Decisões
técnicas" e de "Riscos e mitigação" do plano (docs/plans/NNN-nome.md). Se
alguma decisão virou ADR, referencie o ADR em vez de repetir o raciocínio.
Omita decisões triviais/óbvias — só as que alguém revisando o PR
razoavelmente perguntaria "por que assim e não de outro jeito?".
-->

## Test plan

<!--
Checklist do que foi de fato rodado e validado nesta sessão — não do que o
plano previu rodar. Marque `- [x]` só para o que realmente rodou e passou;
`- [ ]` para o que ficou pendente, com uma linha dizendo por quê. Fontes
típicas: resultado de `npm run lint`, `npm run test:coverage`, `npm run
build`, e da validação manual via o driver de navegador de
`run-<projeto>`, se existir.
-->

## Notas / follow-ups conhecidos

<!--
Opcional — só inclua se houver algo real: desvios do plano descobertos
durante a implementação (já devem estar em "Notas de execução" das tasks),
limitações conhecidas, ou trabalho intencionalmente deixado de fora do
escopo desta feature. Remova a seção inteira se não houver nada aqui.
-->

---

<!--
Rodapé fixo: links para os três documentos SDD (mesmo que já linkados no
Resumo, repetir aqui facilita achar rápido) e a atribuição da sessão atual.
A atribuição NUNCA é fixa neste template — segue sempre a instrução de
atribuição vigente na conversa que está rodando esta skill (session id,
nome do modelo), nunca um valor herdado de uma sessão anterior.
-->

Spec: `docs/specs/NNN-nome.md` · Plano: `docs/plans/NNN-nome.md` · Tasks:
`docs/tasks/NNN-nome.md`
