# Checklist — resultados trimestrais de empresas (ITR, release, teleconferência)

Base numérica: `cvm_cia.py resumo` (trimestres isolados + LTM). Detalhe,
ajustes e contexto: release (`documentos.py cia TICKER --tipo release`) e
notas explicativas. Use pelo menos 8 trimestres e o LTM.

## 1. Receita

- Crescimento a/a (mesmo tri do ano anterior) e t/t (sazonalidade!).
- Origem: volume, preço, câmbio ou aquisições (release).
- Composição por segmento, região e produto; recorrente x pontual.

## 2. Margens e lucro

- Margem bruta, EBITDA, EBIT e líquida — tendência, não o número isolado.
- **EBITDA ajustado** do release x EBITDA calculado pelo script (EBIT + D&A):
  liste o que foi ajustado e se os "não recorrentes" se repetem trimestre a
  trimestre (se repete, é recorrente).
- SG&A crescendo acima da receita (`cvm_cia.py contas TICKER --codigos 3.04.01,3.04.02`).
- Eventos não recorrentes: venda de ativos, créditos tributários,
  impairment, reversões de provisão.
- Lucro líquido, LPA, resultado financeiro, **alíquota efetiva** (JCP,
  incentivos, prejuízo fiscal; alíquota muito baixa/alta pede explicação).

## 3. Caixa

- **FCO x lucro líquido** (qualidade do lucro; FCO/LL persistentemente < 1 é
  alerta).
- Capex de manutenção x expansão (release); fluxo de caixa livre.
- Capital de giro: prazos de recebimento, estoque e fornecedores (variações
  em 6.01.02 da DFC; `plano TICKER --demonstracao DFC --nivel 3`).
- **Risco sacado / forfait**: dívida disfarçada em fornecedores (caso
  Americanas). Busque "risco sacado", "forfait", "convênio", "cessão de
  fornecedores" no release e notas; fornecedores crescendo bem acima do CPV
  é sinal.

## 4. Endividamento e balanço

- Dívida líquida/EBITDA (script usa empréstimos e financiamentos, **sem**
  arrendamentos) x a definição de covenant da empresa (release/notas).
- Cronograma de amortização e risco de refinanciamento.
- Custo e indexação (CDI, IPCA, câmbio); exposição cambial sem hedge.
- Liquidez corrente, goodwill/ágio (risco de impairment), contingências
  (prováveis x possíveis).

## 5. Retorno e acionista

- ROE (script: LL LTM / PL fim) e ROIC x WACC (ROIC pede NOPAT e capital
  investido — calcule se o usuário quiser, deixando premissas explícitas).
- Dividendos/JCP: payout e sustentabilidade frente ao FCL (`cotacao.py
  --dividendos` + FCL LTM); recompras, emissões, planos de ações (diluição).

## 6. Indicadores por setor

- **Bancos**: margem financeira (NII), NPL 90, custo do crédito, Basileia/CET1,
  índice de eficiência, ROE. EBITDA e dívida líquida não se aplicam.
- **Varejo**: vendas mesmas lojas (SSS), vendas/m², giro de estoque,
  e-commerce (GMV, 1P x 3P), antecipação de recebíveis no FCO.
- **Commodities**: volume, preço realizado, custo caixa por unidade, câmbio.
- **Elétricas/saneamento**: revisões tarifárias, perdas, RAB, RAP.
- **Tecnologia/SaaS**: ARR, churn, NRR, CAC, LTV.
- **Seguradoras**: sinistralidade, índice combinado, resultado financeiro.
- **Construtoras**: lançamentos, VSO, distratos, banco de terrenos, margem REF.

**Antes de marcar um indicador do setor como `n/d`**, procure no documento
atual com `pdf_texto.py ARQ.pdf --buscar "<termos>" --contexto 1` (restrinja
com `--paginas` à parte em português, se o release for bilíngue). Termos
sugeridos (radicais; a busca ignora acento e maiúscula):

| Setor | Termos para `--buscar` |
| --- | --- |
| Bancos | `eficiencia,inadimpl,npl,custo do credito,basileia,capital principal,margem financeira,rspl,roae` |
| Seguradoras | `sinistralidade,indice combinado,premios ganhos,resultado financeiro` |
| Varejo | `mesmas lojas,sss,vendas por m,giro,estoque,gmv,1p,3p,antecipa` |
| Commodities | `volume,preco realizado,custo caixa,c1,cash cost,cambio` |
| Elétricas | `revisao tarifaria,reajuste,rap,bar,base de remuneracao,perdas,pmso` |
| Saneamento | `perdas,indice de atendimento,cobertura,ligacoes,base de remuneracao,brr,revisao tarifaria,reajuste` |
| Tecnologia/SaaS | `arr,mrr,churn,nrr,cac,ltv,recorrente` |
| Construtoras | `lancamento,vso,distrato,banco de terrenos,landbank,margem ref,repasse` |

Só marque `n/d` se a busca não achar nada; nesse caso, diga "não
informado no release" (e não apenas "n/d").

## 7. Qualitativo e valuation

- Mensagem da administração e teleconferência; histórico de cumprimento de
  guidance.
- Notas explicativas: partes relacionadas, mudanças contábeis,
  contingências, eventos subsequentes.
- **Auditor**: tipo de parecer/revisão por período (sai no `resumo`),
  menção a ênfase ou incerteza de continuidade, troca de auditor; trocas de
  CEO/CFO (fatos relevantes).
- Múltiplos: P/L, EV/EBITDA (EV = valor de mercado + dívida líquida), P/VP,
  dividend yield, FCF yield — x histórico e pares (`cvm_cia.py pares` para
  os candidatos; confirme os comparáveis com o usuário).

## 8. Sinais de alerta comuns

Lucro sem caixa · dívida crescente · margens em queda · muitos ajustes no
EBITDA · capital de giro deteriorando · fornecedores inflando · alíquota
anômala · notas explicativas confusas · troca de auditor/diretoria.

## 9. Boas práticas

- ≥ 8 trimestres de histórico e números LTM.
- O mercado reage ao resultado **x consenso**, não ao número isolado — sem
  consenso fornecido pelo usuário, não afirme se "veio acima/abaixo do
  esperado".
