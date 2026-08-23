---
name: novas-tasks
description: Quebra um plano técnico aprovado em tasks executáveis em docs/tasks/, seguindo o template do projeto. Use quando o usuário pedir para quebrar um plano em tasks, gerar a lista de tasks, ou avançar de plano para tasks no fluxo Spec → Plano → Tasks → Implementação.
---

Ajuda a quebrar um plano técnico já existente em `docs/tasks/NNN-nome.md`,
seguindo `docs/sdd/workflow.md` e o template `docs/tasks/_template.md`. Ao
contrário das skills de spec/plano, essa etapa é mais mecânica — as decisões
já foram tomadas no plano; o trabalho aqui é sequenciar e dimensionar as
tasks direito. Esta skill só cuida das **tasks** — não implementa.

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
   plano — não descrições vagas tipo "implementar backend".
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

## Passo 4 — Fechar o loop

- Rode `npx prettier --write docs/tasks/NNN-*.md` para manter a formatação
  consistente com o resto do repo.
- Resuma para o usuário a lista de tasks e a ordem escolhida, e pergunte se
  quer ajustar algo antes de começar a implementação.
- **Não** implemente automaticamente — ofereça como próximo passo, só
  comece se o usuário pedir.
