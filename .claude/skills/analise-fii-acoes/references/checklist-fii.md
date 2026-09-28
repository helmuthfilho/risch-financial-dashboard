# Checklist — relatórios de FIIs

Para cada item: onde achar o dado (script/documento) e o que caracteriza
alerta. Item sem dado → "pergunta em aberto".

## 1. Resultado e rendimentos

- **Resultado caixa x distribuição** — `cvm_fii.py trimestral` (Res.tri caixa,
  Acum.caixa, Declarados, Decl/acum). Distribuir acima do resultado consome
  reserva; recorrente > 100% é alerta.
- **Recorrente x não recorrente** — aluguel e juros de CRI x ganho de capital
  (venda de imóvel/cotas), multas rescisórias. No trimestral: Res.TVM inclui
  venda de cotas de FII; no relatório gerencial, procure "ganho de capital",
  "venda", "multa". Distribuição sustentada por ganho não recorrente é alerta.
- **Reserva acumulada não distribuída** — relatório gerencial (resultado
  acumulado/reserva por cota); coluna Retido do trimestral.
- **Regra dos 95%** do lucro caixa semestral — Decl/acum no fim do semestre
  (2T/4T) abaixo de 95% precisa de explicação.
- **Guidance x realizado** — compare o guidance de rendimento do relatório
  anterior com o distribuído.

## 2. Fundos de tijolo

- **Vacância física e financeira** — trimestral traz vacância física por
  imóvel e % da receita; financeira vem do relatório gerencial. Compare com a
  região/segmento (relatório ou pares).
- **Inadimplência e renegociações** — trimestral (% por imóvel) + busca por
  "inadimpl", "renegoci", "acordo".
- **Concentração** — maior imóvel e maior inquilino em % da receita
  (trimestral). >20–25% num único inquilino/imóvel merece destaque.
- **Contratos** — típicos x atípicos, **WAULT** (prazo médio remanescente),
  vencimentos e revisionais nos próximos 12–24 meses (trimestral: vencimento
  por faixa), indexador IPCA x IGP-M.
- **Qualidade dos ativos** — localização, padrão (AAA/A/B), idade, capex
  necessário (relatório gerencial).
- **Preço implícito por m²** = (valor de mercado + dívidas) / ABL, comparado
  com custo de reposição e transações recentes citadas no relatório.
- **Carências e descontos** concedidos (busca por "carência", "desconto").

## 3. Fundos de papel (CRIs)

- **Indexadores** (CDI x IPCA+) e **taxa média** da carteira — relatório
  gerencial.
- **Qualidade de crédito** — high grade x high yield, LTV, garantias
  (alienação fiduciária, cessão de recebíveis, fundo de reserva),
  subordinação.
- **Concentração** por devedor, securitizadora, setor e segmento
  (`cvm_fii.py trimestral` → carteira por emissor; relatório).
- **Eventos de crédito** — atrasos, renegociações, execução de garantias,
  provisões (busca por "atraso", "inadimpl", "waiver", "provis", "execu").
- **Inflação acumulada ainda não distribuída** (fundos IPCA+ que distribuem
  só o caixa recebido).

## 4. Fundos de fundos (FoFs)

- Alocação tijolo x papel; desconto/prêmio sobre o VP dos fundos investidos.
- Peso do **ganho de capital** no resultado (Res.TVM alto x Aluguel/CRI).
- Duplicidade de taxas (taxa do FoF + taxas dos investidos).

## 5. Estrutura, valor e governança

- **Alavancagem** — obrigações por aquisição de imóveis, CRIs emitidos pelo
  fundo (securitização), dívidas (`cvm_fii.py mensal`: Obrig.aquis+secur. e
  obrigações/PL). Cronograma e custo no relatório.
- **Caixa parado / cash drag** após emissões (Caixa+RF alto por meses).
- **Emissões** — preço de emissão x VP (diluição se abaixo do VP), destino
  dos recursos (`mensal` detecta aumento de cotas; confira o fato relevante).
- **P/VP** (preço / VP-cota), **DY** 12m x NTN-B, CDI e pares; premissas das
  reavaliações (cap rate) — reavaliação para cima sem transação que a
  suporte é ponto de atenção.
- **Taxas** (administração, gestão, performance) e alinhamento da gestora;
  **partes ligadas / conflitos** (compra de ativos de fundos da mesma
  gestora, CRIs estruturados pela casa), transparência, pautas de
  assembleia.
- **Liquidez** diária e número de cotistas (`mensal`).

## 6. Documentos e coerência

- Relatório gerencial, informes mensal/trimestral/anual, demonstrações
  auditadas (ressalvas), fatos relevantes, regulamento.
- Confira se o relatório gerencial bate com os informes oficiais: resultado
  e rendimento distribuído, VP/cota, vacância, número de cotistas.
