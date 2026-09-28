# Fontes de dados — detalhes e limitações

Consulte quando um número parecer estranho, faltar, ou antes de afirmar
algo que depende de como o dado foi construído.

## brapi.dev (`cotacao.py`)

- Token em `BRAPI_TOKEN` no `.env`, enviado no header `Authorization: Bearer`
  (nunca na URL). Sem token, só alguns tickers de teste respondem.
- Plano gratuito (verificado em 27/09/2026): **sem proventos** (dividendos/
  JCP exigem o plano Startup), histórico só `range` 1d/5d/1mo/3mo com
  `interval` 1d, e **um ticker por chamada**. Fundamentos (P/L, LPA)
  respondem, mas vêm vazios para FIIs.
- O script se adapta sozinho: lê a mensagem de erro, grava o limite em
  `.cache/analise-fii-acoes/brapi/plano.json` (7 dias) e refaz a chamada sem
  o recurso, com o maior range/intervalo permitido ou um ticker por vez. As
  linhas `Nota:` da saída dizem o que foi ajustado. Se você mudar de plano,
  apague `plano.json` para ele reaprender. Histórico diário longo é
  amostrado (~24 linhas, sempre com o último pregão).
- `BRAPI_PLANO=gratuito` no `.env` carrega esses limites de antemão
  (nenhuma chamada desperdiçada). Vazio = modo de aprendizado.
- Cache local das respostas: 15 min (`--max-idade`).
- Valor de mercado: units (ex.: TAEE11) vêm sem; `proventos.py cia` usa o
  de outra classe da mesma companhia (TAEE3), que é o da companhia inteira.

## Proventos (`proventos.py`)

- **FII**: avisos "Rendimentos e Amortizações" do FundosNET, categoria
  "Aviso aos Cotistas - Estruturado" — XML de ~1 KB por aviso, com
  data-base, valor por cota, data de pagamento, período de referência e
  isenção de IR. É a fonte oficial do valor pago. Cache permanente por
  aviso; a primeira consulta de um fundo leva ~1 min (FundosNET), as
  seguintes ~2 s. Amortização é devolução de capital: aparece separada e
  fica fora do DY. Reapresentação do mesmo provento: vale a entregue por
  último.
- **Aviso que não baixa** (FundosNET oscila): o script tenta de novo numa
  segunda rodada. Se ainda faltar algum, a saída começa com `INCOMPLETO:`
  (ids e datas), a soma e o **DY 12m saem `n/d`** e o DY do último
  rendimento só é mostrado se o aviso faltante for mais antigo que ele.
  Nunca use o valor "parcial" como DY 12m; rode de novo mais tarde ou
  informe `n/d` com o motivo.
- **Empresa**: não há aviso estruturado por ação (o "Aviso aos acionistas"
  do IPE é PDF livre). O DY é **aproximado**: dividendos + JCP pagos a
  acionistas da companhia nos últimos 4 trimestres (DFC, contas 6.03
  escolhidas pelo nome, excluindo não controladores) / valor de mercado
  atual. Mede caixa pago, não proventos por data-com: pagamentos
  concentrados num trimestre (ex.: ITUB4 no 4T) ou atrasados distorcem;
  JCP entra bruto.
- Cotação com atraso ~15 min. `regularMarketTime` diz a hora da cotação.
- **DY 12m** do script = soma dos proventos com data-com nos últimos 365 dias
  / preço atual. JCP entra bruto (sem IR de 15%). FIIs: rendimentos isentos
  para PF (regras vigentes); confira se houver mudança tributária.
- `priceEarnings`/`earningsPerShare` vêm da brapi (critério deles); para
  análise, prefira LPA/lucro LTM da CVM.
- Histórico longo além do plano: alternativa é `yfinance` (sufixo `.SA`),
  não oficial — só se o usuário pedir.

## CVM — FII (`cvm_fii.py`)

- Base: `dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL` e `INF_TRIMESTRAL`
  (ZIP anual; defasagem de semanas). Reapresentações: o script usa a maior
  versão de cada data.
- Ticker → fundo pelo ISIN (`BR` + 4 letras + `CTF...`). Pode haver mais de
  um fundo/classe com o mesmo prefixo (o script avisa e usa o mais recente).
- **Segmento/mandato são autodeclarados** e às vezes errados ou genéricos
  (ex.: MXRF11, de papel, declarado "Logística"; HGLG11 e BTLG11, logísticos,
  declarados "Multicategoria"). Confirme pela composição do ativo; em
  `pares`, use `--segmento` e olhe também o segmento genérico.
- `DY mês` e `Rent.patr.` são percentuais **informados** pelo administrador,
  com base que pode ser o VP e não o preço de mercado.
- Trimestral: `Resultado_Trimestral_Liquido_Financeiro` é do trimestre;
  `Resultado_Financeiro_Liquido_Acumulado` e `Rendimentos_Declarados` são
  **acumulados no semestre** (zeram em jan/jul). `Decl/acum` ~ payout do
  semestre até ali.
- Vacância do informe é **física por imóvel**; vacância financeira só no
  relatório gerencial. Inadimplência por imóvel costuma vir zerada mesmo
  quando há problema — cruze com o relatório.
- Carteira (`ativo`) lista CRIs, cotas de FII, ações de SPEs etc. com valor
  contábil; LTV, garantias e taxa dos CRIs não estão lá (relatório).

## CVM — companhias (`cvm_cia.py`)

- ITR (trimestral) e DFP (anual) padronizados, consolidados por padrão
  (`--individual` para a controladora). FCA dá ticker → CNPJ; cadastro dá
  setor, controle e auditor atual; `parecer` dá o tipo de relatório do
  auditor por período.
- Trimestres isolados: DRE usa a coluna de 3 meses do ITR; 4º tri = DFP − 9M;
  DFC e DVA (só acumulados) são diferenciados trimestre a trimestre. Se um
  trimestre intermediário faltar, o valor isolado fica "-".
- **EBITDA** = EBIT (conta "Resultado Antes do Resultado Financeiro e dos
  Tributos") + D&A da DVA. Não é o EBITDA ajustado do release nem
  necessariamente o EBITDA ICVM 527 (que parte do lucro líquido; em geral
  bate).
- **Dívida bruta** = Empréstimos e Financiamentos CP + LP. Não inclui
  arrendamentos (IFRS 16), debêntures classificadas em outra linha, risco
  sacado nem derivativos. Para Petrobras, por exemplo, arrendamentos são
  mais da metade da dívida bruta do release.
- **Capex** = saídas em contas de imobilizado/intangível da DFC (heurística
  por nome da conta).
- **Contas não fixas mudam de código entre períodos** (ex.: TAEE11, dividendos
  pagos em 6.03.09 nos ITRs de 2025 e em 6.03.07 na DFP). Para elas (capex,
  proventos), o script escolhe as contas pelo nome dentro de cada período
  antes de diferenciar os acumulados. `contas --codigos` usa o código
  literal; para contas não fixas use `contas --nome "regex" --prefixo X`,
  que escolhe pelo nome em cada período e lista os códigos usados. Sem
  `--prefixo`, o nome pode casar contas de grupos diferentes (ex.:
  dividendos *recebidos* em 6.01 x *pagos* em 6.03) — o script avisa.
- Algumas empresas preenchem a divisão lucro dos controladores ×
  minoritários com 0 (ex.: Sabesp até 1T26); o `resumo` mostra "-" nesses
  trimestres, com nota, e o lucro total vale.
- **ROE** = LL LTM / PL do fim do período (não médio). LL inclui
  minoritários; a linha "LL controladores" aparece quando existe.
- **Parecer do auditor** (`resumo`, linha "Auditor por período"): tipo do
  relatório (sem ressalva, com ressalva, adverso, abstenção) + ênfase com
  tema ("ênfase: Valores comparativos"; sem título, "ver Nota X") +
  "incerteza relevante sobre continuidade" quando houver o parágrafo real.
  Várias linhas do mesmo período são combinadas (vale o pior tipo). Ênfase
  não é ressalva: leia o tema. Ex.: em 2025, bancos (Itaú, BB) tiveram
  ênfase técnica pela dispensa de números comparativos na transição para a
  Resolução CMN 4.966 — informativa, não sinal de problema.
- **Holdings** (ex.: BB Seguridade, Caixa Seguridade, Itaúsa): reconhecidas
  quando a receita é zero ou quando a equivalência patrimonial é ≥30% do
  lucro *e* ≥50% do EBIT (12m). O `resumo` mostra "Equivalência
  patrimonial" e "% do lucro", omite margens, EBITDA, capex, FCO/lucro e
  DL/EBITDA, e mantém caixa, dívida e liquidez (holdings podem ter dívida
  própria). Dividendos recebidos das investidas ficam no fluxo de
  investimento: `contas TICKER --nome "dividend" --prefixo 6.02`.
- **Seguradoras** são reconhecidas pelo plano de seguradora (BB Seguridade)
  ou por contas de prêmios/receita de seguro dentro da receita no plano
  comercial (Porto). Indicadores do setor (sinistralidade, índice
  combinado) vêm do relatório de desempenho.
- Bancos/seguradoras: plano de contas diferente; o resumo mostra só receita,
  IR, lucro, FCO, PL e ROE. Indicadores do setor vêm do release.
- Empresas com exercício social fora do ano civil funcionam, mas os rótulos
  "1T..4T" seguem o mês calendário do fim do período.

## Documentos

- **FundosNET** (`fnet.bmfbovespa.com.br`): busca JSON + download de PDF.
  **Não é API oficial**: pode mudar sem aviso e oscila (0,1 s a 60 s por
  resposta). O script usa timeout curto, retry, cache de 30 min da busca e
  1 s entre requisições. Documentos com status "Inativo" (substituídos por
  reapresentação) são omitidos.
- **IPE/CVM**: índice anual em CSV com link para o RAD. O resultado
  trimestral aparece como "Press-release" (release de imprensa, às vezes só
  2–6 páginas) e/ou "Relatório de Análise Gerencial" (relatório completo de
  desempenho / MD&A, dezenas de páginas), ambos na categoria "Dados
  Econômico-Financeiros". `--tipo release` prefere o relatório completo
  quando existe (ex.: BB, BB Seguridade) e ignora versões em inglês
  publicadas como "Comunicado ao Mercado" e informativos mensais.
  Apresentações ficam em "Apresentações a analistas".
- **Duplicatas** (`documentos.py`): o IPE tem várias entradas para o mesmo
  release, como reapresentações (às vezes com data de referência diferente,
  ex. 30/03 e 31/03), versões PT/EN e, no 4º tri, o relatório da
  administração na mesma categoria. O script agrupa por trimestre e escolhe
  PT, depois assunto de release/resultado, depois a entrega mais recente. Se
  o escolhido parecer errado (ex.: empresa que só publica em inglês ou com
  assunto genérico), liste com `--todas-versoes` e baixe por `--ids`.
- Sites de RI: cada empresa tem um formato — não há scraper genérico. Se o
  documento necessário só existir lá, peça ao usuário para anexar o PDF.

## Anexos do usuário

- PDF: `pdf_texto.py` (mapa → páginas). Escaneado ou gráfico:
  `pdf_texto.py --imagem N [--recorte ...]` e ler o PNG (Read direto no PDF
  depende do poppler).
- Planilha `.csv`: pode ler direto se pequena; `.xlsx`: peça exportação para
  CSV ou leia só as abas/colunas necessárias.
- Imagem de tabela: ler a imagem; confira totais (soma das linhas) porque
  OCR visual pode errar dígitos.
