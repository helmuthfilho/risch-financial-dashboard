# Formato da resposta — análise completa

Toda análise completa segue **exatamente** esta estrutura, nesta ordem, para
que análises de ativos diferentes (ou do mesmo ativo em datas diferentes)
sejam comparáveis linha a linha. Pergunta pontual não usa este modelo:
responda direto, com fonte e data.

## Estrutura (ordem fixa)

```markdown
## <TICKER> — <nome> (<tipo: tijolo | papel | FoF | híbrido | setor da empresa>) · dados até <data do dado mais recente>

**Resumo em 3 linhas**
- <o fato mais importante sobre geração de resultado/renda>
- <o principal risco ou dependência>
- <valuation e posição relativa aos pares, sem veredito>

| Indicador | Valor | Tendência / comparação | Fonte (data) |
| --- | --- | --- | --- |
<linhas do modelo do tipo de ativo, na ordem abaixo>

### Promessa × entrega (<documento anterior> → <documento atual>)
| O que foi dito | O que aconteceu | Avaliação |
| --- | --- | --- |

### Pontos positivos
### Pontos de atenção
### Possíveis problemas
### Perguntas em aberto
1. ...

**Coerência <documento> × CVM**
- **Batem:** ...
- **Divergem:** ...

**Fatos relevantes (12 meses):** ...

<sub>Fontes: ... · Cotação com atraso ~15 min · Não é recomendação de investimento.</sub>
```

## Regras gerais

- **Linhas obrigatórias e na ordem do modelo.** Indicador sem dado: a linha
  fica, com `n/d` no Valor e o motivo em Tendência ("não informado no
  relatório", "fora do plano da brapi"), e vira item em Perguntas em aberto.
  Não remova linhas.
- **Linhas extras**: no máximo 3, **no fim** da tabela, só para algo
  específico e material do ativo (ex.: "Venda de ativo no período",
  "Obras em andamento"). Não insira no meio.
- **Valor**: número com unidade (R$/cota, %, x, R$ mi). Dois números na
  mesma linha, separados por ` · ` e na ordem do nome da linha (ex.:
  "2,9% · 3,4%" para "Vacância física · financeira").
- **Tendência / comparação**: a série curta ("0,07 → 1,09 → 0,93") ou
  "vs. pares: A 0,93 · B 0,88". Para P/VP e DY, os pares vão sempre aqui.
- **Fonte (data)**: fonte + mês/trimestre de referência. Valor calculado
  pelo script ou por você → "calculado (<insumos>)".
- **Pontos positivos / atenção / problemas**: 3 a 6 itens cada, cada item
  começando por um **título curto em negrito** seguido do fato com número
  e fonte. "Atenção" = merece acompanhamento; "problema" = pode afetar
  rendimento, valor ou direitos do investidor se se confirmar.
- **Perguntas em aberto**: numeradas, cada uma respondível pelo RI/gestora
  ou pelo próximo documento. Inclua uma para cada linha `n/d` relevante.
- **Promessa × entrega**: uma linha por previsão do documento anterior
  (guidance, prazos, vacância, emissões, desalavancagem). Avaliação com
  exatamente um destes: ✅ cumprido/melhor · ≈ parcial ou desvio explicado
  · ⚠️ em risco/acompanhar · ❌ não cumprido. Se o anterior não trouxe
  previsões, mantenha o título e escreva uma linha: "O documento anterior
  não trouxe guidance nem previsões." Sem documento anterior: "Documento
  anterior indisponível (<motivo>)."
- **Proventos (dividendos, JCP, rendimentos, amortizações)**, em qualquer
  lugar da resposta (tabela, promessa × entrega, pontos):
  - diga sempre o **período de resultado a que se referem** ("sobre o
    resultado do 1S26", "referente a agosto/26"), não só a data do evento;
  - diga se o evento é **declaração/aprovação** ou **pagamento**, que
    costumam cair em datas e até anos diferentes;
  - nunca junte na mesma linha proventos de períodos diferentes, e não
    trate "pagou o antigo" como "manteve a prática";
  - no DY, diga de quais proventos ele vem (período de referência e datas
    de pagamento), para ficar claro se reflete o passado ou o ritmo atual.
  Exemplo: "**Pagamento** em 26/06/26 do JCP **sobre o resultado de 2025**
  (já declarado)" e, em outra linha, "JCP **sobre o resultado do 1S26**:
  **não declarado** (Conselho, 24/06/26)".
- **Coerência × CVM**: sempre presente. Divergência com os dois valores, as
  duas fontes e o motivo provável (data diferente, método, campo não
  atualizado).
- **Fatos relevantes**: um parágrafo — quantos houve em 12 meses, quais foram
  abertos (data — assunto) e por que os demais não foram.
- **Sem comentários sobre a skill, os scripts ou o processo** na resposta
  (tempo de download, limitações de ferramenta etc.). Limitação que afeta
  um número vai na linha dele (Tendência ou Fonte), não em bloco à parte.
- Sem veredito ("barato", "compre"); comparação com histórico e pares.

## Modelos de tabela de indicadores

### FII de tijolo

| # | Indicador | Origem típica |
| --- | --- | --- |
| 1 | Preço | `cotacao.py` |
| 2 | VP/cota | `cvm_fii.py mensal` (tendência 24m) |
| 3 | P/VP | calculado; pares |
| 4 | Rendimento atual (R$/cota) | `proventos.py fii` |
| 5 | DY 12m · DY atual ×12 | `proventos.py fii`; pares |
| 6 | Resultado recorrente (R$/cota) | relatório gerencial |
| 7 | Payout (distribuído ÷ resultado caixa) | `cvm_fii.py trimestral`; relatório |
| 8 | Reserva acumulada (R$/cota) | relatório gerencial |
| 9 | Vacância física · financeira | relatório; CVM trimestral |
| 10 | WALE · % da receita vencendo em 12m | relatório; CVM trimestral |
| 11 | Indexadores (% IPCA · % IGP-M) | CVM trimestral |
| 12 | Alavancagem (% PL) | CVM mensal; relatório |
| 13 | Concentração (maior imóvel · maior setor de inquilinos) | CVM trimestral |
| 14 | Emissões nos últimos 24m | CVM mensal; fatos relevantes |
| 15 | Taxa de administração | relatório; CVM mensal |
| 16 | Cotistas · liquidez diária média | CVM mensal; relatório |

### FII de papel

Linhas 1–8 iguais às do tijolo, depois:

| # | Indicador | Origem típica |
| --- | --- | --- |
| 9 | Composição (% CRI · % caixa · % cotas de FII) | CVM mensal |
| 10 | Indexadores da carteira (% CDI · % IPCA+) e taxa média | relatório |
| 11 | Qualidade de crédito (% high grade · LTV médio) | relatório |
| 12 | Maior devedor · maior securitizadora (% carteira) | CVM trimestral; relatório |
| 13 | Eventos de crédito (atrasos, renegociações, provisões) | relatório; fatos relevantes |
| 14 | Inflação acumulada a distribuir (R$/cota) | relatório |
| 15 | Alavancagem (compromissadas/obrigações % PL) | CVM mensal; relatório |
| 16 | Taxa de administração · cotistas · liquidez diária | CVM mensal; relatório |

### FoF

Linhas 1–8 iguais às do tijolo, depois:

| # | Indicador | Origem típica |
| --- | --- | --- |
| 9 | Alocação (% tijolo · % papel · % caixa) | relatório; CVM mensal |
| 10 | Desconto/prêmio médio sobre o VP dos investidos | relatório |
| 11 | Peso do ganho de capital no resultado 12m | relatório; CVM trimestral (Res.TVM) |
| 12 | Maior posição (% carteira) | CVM trimestral |
| 13 | Taxas (do FoF · estimativa das investidas) | relatório |
| 14 | Alavancagem · cotistas · liquidez diária | CVM mensal; relatório |

### FII híbrido

Modelo de tijolo (1–16) + linhas 10–13 do modelo de papel ao fim, para a
parcela em CRIs (numeradas 17–20).

### Empresa (não financeira)

| # | Indicador | Origem típica |
| --- | --- | --- |
| 1 | Preço · valor de mercado | `cotacao.py --fundamentos` |
| 2 | Receita (último tri · a/a · LTM) | `cvm_cia.py resumo` |
| 3 | Margem bruta · EBITDA · líquida (LTM, tendência 8 tri) | `resumo` |
| 4 | EBITDA ajustado (release) × EBITDA calculado (CVM) | release; `resumo` |
| 5 | Lucro líquido (último tri · a/a · LTM) · LPA | `resumo`; release |
| 6 | FCO ÷ lucro líquido (LTM) | `resumo` |
| 7 | Capex · FCL (LTM) | `resumo` |
| 8 | Dívida líquida · DL/EBITDA LTM (CVM; e com arrendamentos, se o release der) | `resumo`; release |
| 9 | Liquidez corrente | `resumo` |
| 10 | ROE LTM | `resumo` |
| 11 | Alíquota efetiva LTM | `resumo` |
| 12 | DY aproximado 12m · payout (pagos ÷ lucro LTM) | `proventos.py cia` |
| 13 | P/L · EV/EBITDA · FCF yield | calculado |
| 14 | Parecer do auditor (último) · troca de auditor | `resumo` |
| 15–17 | 1 a 3 indicadores do setor (checklist-acoes.md §6) | release |

### Banco / seguradora

| # | Indicador | Origem típica |
| --- | --- | --- |
| 1 | Preço · valor de mercado | `cotacao.py --fundamentos` |
| 2 | Lucro líquido (último tri · a/a · LTM) | `cvm_cia.py resumo` |
| 3 | ROE LTM | `resumo`; release |
| 4 | Banco: margem financeira (NII) · Seguradora: prêmios ganhos | release |
| 5 | Banco: NPL 90 dias · Seguradora: sinistralidade | release |
| 6 | Banco: custo do crédito · Seguradora: índice combinado | release |
| 7 | Banco: Basileia/CET1 · Seguradora: resultado financeiro | release |
| 8 | Índice de eficiência | release |
| 9 | Crescimento da carteira de crédito / prêmios (a/a) | release |
| 10 | P/L · P/VP | calculado |
| 11 | DY aproximado 12m · payout | `proventos.py cia` |
| 12 | Parecer do auditor (último) | `resumo` |

## Comparação entre períodos

Mesma estrutura, com três blocos a mais **depois da tabela de indicadores e
antes de "Promessa × entrega"**, nesta ordem:

1. `### Lado a lado (<N> períodos)` — tabela com uma coluna por período
   (mais antigo → mais recente) e as linhas-chave do modelo do tipo de
   ativo; cada célula que vier do documento (e não da CVM) marcada com `ᴿ`.
2. `### O que mudou no discurso` — temas novos, temas que sumiram, mudança
   de tom (bullets com período e página).
3. `### Ajustes recorrentes` — itens "não recorrentes" que aparecem em mais
   de um período, com valores por período.

"Promessa × entrega" passa a cobrir todos os pares de períodos consecutivos.
