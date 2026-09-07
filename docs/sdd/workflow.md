---
título: Fluxo de Trabalho SDD
atualizado_em: 2026-09-07
---

# Fluxo de Trabalho (Spec-Driven Development)

Fluxo leve, em 4 etapas, para qualquer funcionalidade não-trivial. Correções
pontuais, ajustes de estilo ou bugs pequenos podem pular direto para
implementação.

```
docs/specs/NNN-nome.md   →   docs/plans/NNN-nome.md   →   docs/tasks/NNN-nome.md   →   implementação
     (O QUÊ)                     (COMO)                      (passos)                   (código)
```

## 1. Spec (`docs/specs/NNN-nome.md`)

Descreve **o quê** e **por quê**, nunca **como**. Usa
`docs/specs/_template.md`. Numeração sequencial de 3 dígitos (`001`, `002`, ...)
compartilhada entre specs/plans/tasks do mesmo tema (mesmo número + mesmo nome).

Cobre só **requisitos funcionais** (comportamento observável). Requisitos
não-funcionais (desempenho/volume, segurança/privacidade, etc.) não são
levantados aqui — isso é responsabilidade do plano técnico, para não
entrevistar o usuário duas vezes sobre o mesmo assunto em etapas diferentes.

Deve ser possível ler uma spec sem saber nada de código.

## 2. Plano técnico (`docs/plans/NNN-nome.md`)

Descreve **como** implementar a spec correspondente: arquitetura, modelo de
dados, decisões técnicas, alternativas consideradas e riscos. Usa
`docs/plans/_template.md`. Referencia explicitamente a spec de origem.

Também é onde os **requisitos não-funcionais** da feature são levantados e
registrados (seção "Requisitos não-funcionais" do template) — a spec só
traz o funcional.

Decisões arquiteturais que sobrevivem além de uma única feature (ex.: escolha
de banco de dados, framework, estratégia de autenticação) viram um ADR em
`docs/adr/` em vez de ficarem soterradas num plano específico.

## 3. Tasks (`docs/tasks/NNN-nome.md`)

Quebra o plano em passos pequenos e verificáveis, em ordem de execução. Usa
`docs/tasks/_template.md`. Cada task deve ser pequena o suficiente para revisar
em um único diff.

## 4. Implementação

Só começa depois que spec + plano estiverem estáveis o bastante (não precisam
ser "perfeitos", mas as perguntas em aberto relevantes precisam estar
resolvidas). Implementação segue a ordem das tasks; desvios do plano durante a
implementação devem ser refletidos de volta no plano ou registrados como nota.

## Quando pular etapas

- **Bug fix pontual / typo / ajuste de estilo:** implementa direto, sem spec.
- **Mudança pequena dentro do escopo de uma spec já aprovada:** pode pular
  direto para uma task nova no arquivo de tasks existente, sem nova spec.
- **Qualquer coisa que mexa em modelo de dados, adicione uma tela/fluxo novo,
  ou introduza uma integração externa:** sempre passa pelo fluxo completo.

## Numeração e status

Cada spec/plano/task tem um cabeçalho com `status` (`rascunho`, `aprovado`,
`em andamento`, `concluído`, `abandonado`). Atualizar o status é parte do
trabalho, não um detalhe.

Ver também: [[constitution]], [[glossary]].
