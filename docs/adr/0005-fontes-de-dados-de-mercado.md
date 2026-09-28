---
número: 0005
título: Fontes de dados de mercado (cotações, informes e documentos)
status: aceito
criado_em: 2026-09-27
---

# 0005 — Fontes de dados de mercado (cotações, informes e documentos)

## Status

Aceito (2026-09-27)

## Contexto

A skill `analise-fii-acoes` (apoio à análise de relatórios de FIIs e
empresas da B3) precisa de cotações, proventos, dados fundamentalistas e
relatórios em PDF. As mesmas fontes tendem a ser reutilizadas pelo
dashboard (ex.: preço atual das posições de renda variável), então a
escolha atravessa mais de uma feature.

Forças em jogo: custo (preferência por gratuito), dados oficiais x
agregadores, estabilidade das interfaces, limites de requisição e o
princípio 2 da constituição (dados sensíveis, segredos fora do git).

## Decisão

- **Cotações e valor de mercado: brapi.dev**, autenticada por token em
  `BRAPI_TOKEN` no `.env` (ignorado pelo git; `.env.example` com valor
  vazio), enviado no header `Authorization: Bearer`, nunca na URL nem em
  logs. O plano contratado é declarado em `BRAPI_PLANO` (hoje `gratuito`),
  para o código já respeitar os limites sem sondar a API; cache local das
  respostas.
- **Proventos: fontes oficiais.** FIIs: avisos de rendimentos estruturados
  (XML) do FundosNET. Companhias: dividendos e JCP pagos na DFC da CVM
  (DY aproximado sobre o valor de mercado). A brapi só é usada para
  proventos se `BRAPI_PLANO` indicar um plano pago que os inclua.
- **Dados estruturados: CVM Dados Abertos** (informes mensal/trimestral de
  FII; ITR, DFP, FCA, cadastro e IPE de companhias) — oficial, gratuito, sem
  cadastro.
- **Documentos PDF: FundosNET (B3)** para FIIs e **IPE/RAD (CVM)** para
  companhias. FundosNET não é API oficial: uso com intervalo entre
  requisições, timeout curto e degradação graciosa (a análise segue com os
  dados da CVM se ele falhar).
- Downloads e cache ficam em `.cache/` na raiz, fora do git.

## Alternativas consideradas

- **yfinance** (não oficial, `.SA`): bom para histórico longo de preços;
  fica como alternativa sob demanda, não padrão.
- **Proventos pela brapi** (plano Startup, pago): daria proventos por
  data-com num só lugar, mas tem custo recorrente; as fontes oficiais
  cobrem o necessário sem custo.
- Alpha Vantage (`.SAO`), HG Brasil Finance, `GOOGLEFINANCE`: cobertura ou
  limites piores para FIIs/proventos brasileiros.
- Scraping de sites de RI: cada empresa tem um formato; custo de manutenção
  alto. Documentos que só existam lá são anexados manualmente pelo usuário.

## Consequências

- Cotação gratuita tem atraso de ~15 min; tempo real oficial da B3 é pago.
- No plano gratuito da brapi (verificado em 27/09/2026) não há proventos,
  o histórico vai até 3 meses com intervalo diário e cada chamada aceita um
  ticker só. Limites e preços mudam: o código tolera recusas (aprende o
  limite pela mensagem de erro e segue com o que o plano permite) e o
  plano deve ser conferido em brapi.dev.
- Proventos de FII vêm do valor oficialmente declarado pelo administrador;
  os de companhias são o caixa pago no período (DFC), não proventos por
  data-com — pagamentos concentrados ou atrasados distorcem o DY.
- Dados da CVM têm defasagem de semanas após o fim de cada período.
- Os scripts atuais vivem na skill (`.claude/skills/analise-fii-acoes/`),
  em Python, e não escrevem no banco do app. Integrar cotações ao dashboard
  (TypeScript, persistência em centavos conforme
  [[0003-dinheiro-como-inteiro-em-centavos]]) é uma feature nova e passa pelo
  fluxo de spec; este ADR só fixa as fontes.

## Histórico

- 2026-09-27: aceito. No mesmo dia, ajustado com o resultado dos testes
  com o plano gratuito da brapi: proventos passaram a vir de fontes
  oficiais (FundosNET e DFC da CVM) e a premissa de "chamadas agrupadas"
  foi substituída pela declaração do plano em `BRAPI_PLANO`. A escolha das
  fontes (brapi, CVM, FundosNET, IPE) não mudou.
