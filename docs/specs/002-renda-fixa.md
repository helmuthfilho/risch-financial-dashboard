---
número: 002
título: Renda Fixa — Cadastro e Acompanhamento de Posições
status: concluído
criado_em: 2026-08-22
atualizado_em: 2026-08-22
---

# 002 — Renda Fixa — Cadastro e Acompanhamento de Posições

## Contexto e motivação

Hoje a página `/renda-fixa` é só um placeholder. O usuário mantém suas
aplicações de renda fixa (CDB, Tesouro Direto, LCI/LCA) espalhadas em
extratos e planilhas separadas, sem uma visão consolidada. Essa spec dá o
primeiro passo: um lugar único para registrar e acompanhar essas posições.

## Objetivo

Permitir que o usuário cadastre manualmente e acompanhe suas posições de
renda fixa (CDB, Tesouro Direto, LCI/LCA), com valor aplicado e valor atual
informados por ele, sem cálculo automático de rendimento.

## Escopo

### Dentro do escopo

- Cadastro manual de uma posição de renda fixa: instituição, tipo de título
  (CDB, Tesouro Direto ou LCI/LCA), descrição/nome do título, data de
  aplicação, valor aplicado, taxa contratada (texto livre, ex.: "110% CDI",
  "IPCA+6%"), data de vencimento.
- Edição e exclusão de uma posição cadastrada.
- Atualização do valor atual de uma posição pelo usuário, preservando
  histórico das atualizações (ver Requisito funcional 3 e [[constitution]]
  item 3 — rastreabilidade).
- Listagem de todas as posições de renda fixa, com valor aplicado, valor
  atual (quando informado) e totais agregados.

### Fora do escopo

- Importação de posições via CSV/extrato de corretora — a exportação de
  dados de renda fixa das corretoras costuma ser ruim/inconsistente demais
  para valer a complexidade agora; cadastro é só manual nesta spec. Fica
  para uma spec futura dedicada, se e quando fizer sentido revisitar.
- Cálculo automático de rendimento com base em indexadores de mercado
  (%CDI, IPCA, etc.), incluindo possível integração futura com alguma API
  que forneça essas taxas — fica para uma spec futura dedicada.
- Debêntures e outros instrumentos de renda fixa não listados acima.
- Integração automática com bancos/corretoras (Open Finance) — já fora de
  escopo por padrão pela [[constitution]] (seção 3).
- Alertas de vencimento e notificações.
- Gráficos de evolução da carteira — fica para uma spec de visualização
  futura, quando houver dados reais o suficiente para justificar.

## Requisitos funcionais

1. Usuário cadastra manualmente uma posição informando: instituição, tipo
   (CDB / Tesouro Direto / LCI/LCA), descrição do título, data de aplicação,
   valor aplicado, taxa contratada (texto livre), data de vencimento.
2. Usuário edita os dados de uma posição existente.
3. Usuário atualiza o valor atual de uma posição; cada atualização fica
   registrada com sua data — o sistema mantém histórico, não sobrescreve o
   valor anterior silenciosamente (ver [[constitution]] item 3).
4. Usuário exclui uma posição.
5. Usuário visualiza uma listagem de todas as posições de renda fixa, com
   instituição, tipo, valor aplicado, valor atual mais recente (se houver) e
   data de vencimento.
6. A listagem mostra o total aplicado somado e o total atual somado (quando
   disponível) de todas as posições de renda fixa.

## Requisitos não-funcionais

- Desempenho / volume de dados esperado: baixo — dezenas a poucas centenas
  de posições para uso pessoal. Não requer otimização especial.
- Segurança / privacidade (ver [[constitution]] item 2): valores e nomes de
  instituição nunca logados em texto claro; nenhuma spec, teste ou exemplo
  versionado usa dados financeiros reais.
- Dinheiro nunca é float (ver [[constitution]] item 1): valor aplicado e
  valor atual armazenados como tipo decimal exato em todas as camadas.
- Moeda: todas as posições de renda fixa são em BRL. Sem suporte a outras
  moedas nesta spec.

## Critérios de aceite

- [x] Cadastro manual funciona com todos os campos obrigatórios validados
      (instituição, tipo, valor aplicado, data de aplicação).
- [x] Edição e exclusão de uma posição refletem corretamente na listagem.
- [x] Atualizar o valor atual de uma posição preserva o histórico de
      atualizações anteriores (não sobrescreve silenciosamente).
- [x] A listagem mostra o total aplicado e o total atual somados
      corretamente.
- [x] Nenhum valor monetário é armazenado ou somado como `float`/`double`
      em nenhuma camada (banco, backend, frontend) — armazenado como
      `bigint` em centavos, ver [[0003-dinheiro-como-inteiro-em-centavos]].

## Desvios da constituição

Nenhum. A spec segue os princípios 1 (Decimal), 2 (dados sensíveis), 3
(rastreabilidade via histórico de atualização de valor) e 4 (single-user
local) de [[constitution]].

## Perguntas em aberto

Nenhuma — as três perguntas originais foram resolvidas em conversa com o
usuário em 2026-08-22: importação de CSV fica fora de escopo por ora (ver
seção Escopo), taxa contratada permanece texto livre por enquanto (com
cálculo automático — possivelmente via integração com API de indexadores —
cogitado para uma spec futura), e a moeda é sempre BRL (ver Requisitos
não-funcionais).
