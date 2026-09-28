---
name: analise-fii-acoes
description: Apoia a leitura e análise de relatórios de Fundos Imobiliários (FIIs) e de resultados trimestrais de empresas listadas na B3 — coleta cotação (brapi.dev), informes estruturados da CVM (informe mensal/trimestral de FII, ITR/DFP de companhias), relatórios gerenciais/releases em PDF (FundosNET, IPE/CVM) e aplica um checklist, devolvendo pontos positivos, pontos de atenção, possíveis problemas e perguntas em aberto. Use quando o usuário pedir para analisar um FII ou uma ação (ex.: "analisa o HGLG11", "o que achou do resultado do 2T26 da PETR4?"), comparar com pares, comparar os últimos relatórios/trimestres de um mesmo ativo ("compara os 3 últimos releases da X"), ler um relatório gerencial/release anexado, ou consultar cotação, proventos, P/VP, DY, vacância, endividamento etc. de ativos brasileiros.
model: opus
effort: high
---

Apoio à **análise** de FIIs e ações brasileiras. **Não é recomendação de
compra ou venda** — o trabalho é levantar pontos, calcular indicadores,
destacar possíveis problemas e perguntas em aberto; o usuário tira as
conclusões. Não diga "compre", "venda", "está barato/caro" como veredito;
compare com histórico e pares e deixe o julgamento explícito para ele.

Roda com `model: opus` e `effort: high` porque o valor está no raciocínio
sobre os números (coerência, tendência, sinais de alerta). A coleta pesada
fica em scripts Python que devolvem tabelas compactas — **nunca** leia CSV,
ZIP ou PDF inteiros na conversa; use os scripts.

## Setup (uma vez)

- Token da brapi: variável `BRAPI_TOKEN` no `.env` da raiz (já no
  `.gitignore`). **Nunca** imprima, ecoe, faça `cat` do `.env` nem passe o
  token por linha de comando; os scripts leem sozinhos.
- Plano da brapi: `BRAPI_PLANO` no `.env` (hoje `gratuito`). Com plano
  declarado, `cotacao.py` já sai ajustado na primeira chamada. Vazio =
  modo de aprendizado (descobre os limites pelos erros).
- Dependência de PDF (só `pdf_texto.py` precisa):
  ```bash
  python3 -m venv .claude/skills/analise-fii-acoes/.venv
  .claude/skills/analise-fii-acoes/.venv/bin/pip install -r .claude/skills/analise-fii-acoes/requirements.txt
  ```
  Os demais scripts são só biblioteca padrão (`python3` >= 3.9).
- Ao alterar os scripts, rode os testes (sem rede):
  `.claude/skills/analise-fii-acoes/.venv/bin/python -m unittest discover -s .claude/skills/analise-fii-acoes/scripts -p "test_*.py"`
- Downloads e cache ficam em `.cache/analise-fii-acoes/` (ignorado pelo git).
  Primeira consulta de empresa baixa ~20 MB/ano de ITR/DFP da CVM (uma vez);
  as seguintes usam cache. Organização, validade de cada arquivo e como
  forçar atualização: `references/cache.md`.
- **Não rode duas execuções dos scripts em paralelo** (ex.: vários pares em
  processos simultâneos): o cache não tem escrita segura para isso e um ZIP
  baixado ao mesmo tempo por dois processos pode corromper. Uma análise por
  vez. Detalhes em `references/cache.md`.

## Scripts

Caminho: `.claude/skills/analise-fii-acoes/scripts/` (abreviado `S/` abaixo).
Rode da raiz do repo. Todos têm `--help`.

| Comando | Devolve |
| --- | --- |
| `python3 S/cotacao.py T1 T2 ... [--fundamentos] [--historico 3mo --intervalo 1d]` | preço, variação, faixa 52s; P/L, LPA, valor de mercado; fechamentos (`--dividendos` só em plano pago) |
| `python3 S/proventos.py fii FII [--meses 12] [--sem-preco]` | rendimentos e amortizações por cota dos avisos oficiais (FundosNET, XML estruturado); DY 12m e DY do último rendimento ×12 |
| `python3 S/proventos.py cia TICKER [--trimestres 4] [--sem-preco]` | dividendos + JCP pagos por trimestre (DFC/CVM) e DY aproximado 12m sobre o valor de mercado |
| `python3 S/cvm_fii.py mensal FII [--meses 24]` | série mensal oficial: PL, VP/cota, cotistas, DY informado, caixa, imóveis, CRI, obrigações; emissões detectadas |
| `python3 S/cvm_fii.py trimestral FII [--trimestres 8] [--top 10]` | resultado caixa x contábil x declarado (payout semestral), imóveis com vacância/inadimplência, inquilinos por setor, vencimentos e indexadores dos contratos, carteira de CRIs/cotas |
| `python3 S/cvm_fii.py pares FII [--top 15] [--segmento Logística]` | fundos do mesmo segmento por PL, com VP/cota, DY, taxa; o fundo analisado na 1ª linha |
| `python3 S/cvm_cia.py resumo TICKER [--trimestres 8]` | trimestres isolados + LTM: receita, margens, EBITDA, lucro, FCO, capex, FCL, DL/EBITDA, ROE, alíquota, liquidez; auditor e tipo de parecer |
| `python3 S/cvm_cia.py pares TICKER [--top 10] [--setor "..."]` | candidatos a par: companhias ativas com ação em bolsa no mesmo setor da CVM (holdings incluídas), por receita da última DFP |
| `python3 S/cvm_cia.py plano TICKER --demonstracao DRE` e `contas TICKER --codigos 3.04.02,...` | plano de contas e contas específicas pelo código (bancos, seguradoras, detalhamentos) |
| `python3 S/cvm_cia.py contas TICKER --nome "regex" [--prefixo 6.03] [--excluir "regex"] [--nivel N]` | contas escolhidas pelo **nome** em cada período (contas não fixas, cujo código muda entre ITR e DFP), com os códigos usados e aviso se a soma mistura grupos |
| `python3 S/documentos.py fii FII [--tipo relatorio\|fato\|rendimento\|informe\|assembleia] [-n N] [--baixar N] [--ids ...]` | lista (id, referência, entrega, tipo) e baixa PDFs do FundosNET, 1 por período |
| `python3 S/documentos.py cia TICKER [--tipo release\|fato\|comunicado\|apresentacao\|dfs\|assembleia\|proventos] [-n N] [--baixar N] [--ids ...]` | idem, pelo índice IPE da CVM (release: 1 por trimestre, relatório completo de desempenho quando existir) |
| `.venv/bin/python S/pdf_texto.py ARQ.pdf --mapa --perfil fii\|cia` | 1 linha por página: título, nº de tabelas, termos do checklist presentes |
| `.venv/bin/python S/pdf_texto.py ARQ.pdf --paginas 4-6` / `--buscar "vacância,carência" --contexto 1` | texto limpo só das páginas/linhas que interessam; `--paginas` também restringe `--mapa` e `--buscar` |
| `.venv/bin/python S/pdf_texto.py A.pdf B.pdf C.pdf --mapa\|--buscar ...` | mesma operação em vários PDFs; `--buscar` termina com tabela termo x arquivo |
| `.venv/bin/python S/pdf_texto.py ARQ.pdf --imagem 9 [--recorte 0.55,0.5,1,0.95]` | salva página(s) como PNG e imprime o caminho; depois leia o PNG com Read |

**Duplicatas em `documentos.py`**: por padrão sai um documento por período
e sempre o mais recente. Release/DFs (cia) e relatório/informe (fii) ficam
com 1 por trimestre/mês. Entre candidatos do mesmo período, a ordem é:
português antes de inglês, depois assunto de release/resultado (e não
relatório da administração), e por fim a entrega mais recente, então a
reapresentação substitui a original. Nos outros tipos, o mesmo documento
reapresentado aparece uma vez. A linha indica `+k versão(ões) omitida(s)`;
`--todas-versoes` mostra tudo. `-n` conta documentos já deduplicados, então
`-n 3 --baixar 3` baixa os últimos 3 trimestres. `--ids` baixa qualquer id,
mesmo fora da lista (empresa: qualquer documento do IPE dos últimos 5 anos).

`--tabelas` no `pdf_texto.py` só ajuda em tabelas com grade desenhada; em
releases, o texto corrido costuma preservar melhor as linhas das tabelas.
Gráficos e PDFs escaneados: quando o texto de uma página vira números soltos
(ex.: gráfico de reserva acumulada, evolução de vacância), gere a imagem com
`pdf_texto.py --imagem N` e leia o PNG com a ferramenta Read. Use `--recorte`
para pegar só o gráfico (menos tokens). Não use Read direto no PDF: ele
depende do poppler, que pode não estar instalado.

**Plano da brapi**: no plano gratuito (verificado em 27/09/2026) **não há
proventos**, o histórico vai até 3 meses só com intervalo diário e cada
chamada aceita um ticker só. Com `BRAPI_PLANO=gratuito` a skill **não pede
proventos à brapi**: a brapi fica só com preço e valor de mercado, e os
proventos vêm de `proventos.py` (fontes oficiais). Se algum limite mudar,
`cotacao.py` não aborta: aprende pela mensagem de erro, segue com o que o
plano permite e avisa nas linhas `Nota:`.

## Fluxo

### 1. Enquadrar

- Ativo(s), período de interesse, e se é análise completa ou pergunta
  pontual. Pergunta pontual ("qual o DY do MXRF11?") → rode só o script
  necessário e responda; não faça a análise completa.
- Escopo pela forma do pedido (inclusive quando invocada direto com
  `/analise-fii-acoes`):
  - só ticker(s), sem pergunta (`/analise-fii-acoes HGLG11`) → análise
    completa de cada ativo;
  - com uma pergunta → responda só a pergunta, com os scripts necessários;
  - com restrição explícita ("sem cotação", "só CVM", "só o relatório") →
    respeite, mesmo que o roteiro padrão incluísse o passo;
  - sem argumento nenhum → pergunte qual ativo e o que o usuário quer ver.
- FII ou empresa: ticker terminado em 11 pode ser FII **ou** unit
  (TAEE11, KLBN11). `cvm_fii.py resolver` falha para units → use `cvm_cia.py`.
- Tipo de FII (tijolo, papel, FoF, híbrido): não confie no "segmento" da CVM
  (é autodeclarado e às vezes errado); infira pela composição do ativo no
  `mensal` (imóveis x CRI x cotas de FII) e pela carteira no `trimestral`.
- Relatório anexado pelo usuário: vá direto ao passo 3 com o arquivo dele,
  mas ainda puxe os dados estruturados para checar coerência.

### 2. Dados estruturados (barato, sempre primeiro)

Períodos padrão da análise completa (use sempre estes, salvo pedido
diferente): **24 meses** no mensal, **8 trimestres** no trimestral/resumo,
**12 meses** de proventos.

- FII: `proventos.py fii FII` (rendimentos oficiais + preço + DY) +
  `cvm_fii.py mensal FII --meses 24` + `cvm_fii.py trimestral FII --trimestres 8`
  (8 já é o padrão do script; o explícito documenta o período). P/VP = preço / VP-cota do
  último informe (diga a data de cada um). Cite o DY 12m e o DY do último
  rendimento ×12 (diferem quando o rendimento mudou no ano), e o DY
  informado à CVM (`mensal`, base patrimonial) como checagem.
- Empresa: `cotacao.py TICKER --fundamentos` + `proventos.py cia TICKER` +
  `cvm_cia.py resumo TICKER --trimestres 8`. O DY de empresa é **aproximado** (caixa pago na DFC /
  valor de mercado); diga isso na resposta.
- Em plano pago (`BRAPI_PLANO` diferente de `gratuito`), `cotacao.py
  --dividendos` também serve, e dá proventos por data-com.
- `cotacao.py` aceita vários tickers; no plano gratuito ele consulta um por
  vez sozinho.

### 3. Documentos (só o necessário)

- Liste e baixe os **dois últimos** documentos do período: `documentos.py fii
  FII -n 2 --baixar 2` (relatório gerencial) ou `documentos.py cia TICKER -n 2
  --baixar 2` (release). A lista já vem com 1 por período, o mais recente.
- **Documento atual** (o mais recente): `--mapa` e leitura das páginas que o
  mapa aponta para os itens do checklist — é a base da análise.
- **Documento anterior**: leitura **restrita** a guidance e resultado, para
  checar promessa x entrega. Não leia o resto dele. Rode o mapa dos dois de
  uma vez (`pdf_texto.py ATUAL.pdf ANTERIOR.pdf --mapa --perfil fii|cia`),
  case as seções pelo título e leia do anterior só:
  - FII: comentários da gestão (guidance de rendimento, movimentações
    previstas de locatários/vacância, emissões/aquisições anunciadas) e a
    página de resultado;
  - empresa: mensagem da administração/destaques e guidance (capex,
    produção, alavancagem, margens), se houver.
  Tipicamente 2–3 páginas. Um `--buscar "guidance,previs,expectativa,estimat"`
  nos dois arquivos ajuda a achar as frases.
- **Release bilíngue** (comum: metade em português, metade tradução em
  inglês): no `--mapa`, a tradução começa onde os títulos passam para o
  inglês ou aparece "free translation". Restrinja mapa, busca e leitura à
  parte em português com `--paginas` (ex.: `--mapa --paginas 1-28`,
  `--buscar "..." --paginas 1-28`) — evita duplicatas e metade dos tokens.
- Se não houver documento anterior (fundo/empresa nova, FundosNET falhou),
  diga isso e siga só com o atual.
- Fatos relevantes dos últimos 12 meses: só listar; abrir os que o título
  indicar evento material (emissão, venda de ativo, evento de crédito,
  renegociação, troca de gestor/auditor).

### 4. Checklist

Leia **só** a referência do tipo de ativo em análise:

- FII → `references/checklist-fii.md`
- Empresa → `references/checklist-acoes.md` (inclui indicadores por setor)
- Formato da resposta (sempre, em análise completa ou comparação) →
  `references/formato-resposta.md`; use o modelo de tabela do tipo de ativo
  identificado no passo 1
- Limitações e detalhes de cada fonte → `references/fontes-de-dados.md`
  (consulte quando um número parecer estranho ou faltar)

Itens do checklist sem dado disponível viram "perguntas em aberto", não
suposições. **Indicadores do setor (empresas)**: antes de marcar `n/d`,
procure no documento atual com `--buscar` e os termos do setor listados em
`references/checklist-acoes.md` §6; `n/d` só depois de a busca não achar, e
com o motivo "não informado no release".

### 5. Pares e coerência

- FII: `cvm_fii.py pares` e, para 3–5 pares relevantes, `cotacao.py` (P/VP) e,
  se o DY dos pares importar, `proventos.py fii PAR` (cada fundo novo custa
  ~1 min de FundosNET na primeira vez). Pares de papel x tijolo não são comparáveis diretamente.
  Se o segmento autodeclarado for genérico ou errado (o script avisa em
  "Multicategoria"/"Híbrido"/"Outros"), rode `pares FII --segmento <real>`
  e também confira o próprio segmento genérico: fundos do segmento real
  costumam estar lá (ex.: BTLG11, logístico, declara "Multicategoria").
  Tire da comparação pares que estejam sendo incorporados pelo fundo
  analisado ou pela mesma gestora (não são independentes).
- Empresa: `cvm_cia.py pares TICKER` lista os candidatos (mesmo setor da
  CVM, com ação em bolsa, por receita). O setor da CVM é amplo — escolha
  entre eles 2–4 comparáveis de verdade (mesmo modelo de negócio e porte
  razoável; ex.: PETR4 → PRIO3/BRAV3 são produtoras, UGPA3 é distribuidora),
  **proponha ao usuário e confirme** antes de rodar `cvm_cia.py resumo` para
  cada um. Se o usuário já disse os pares, use os dele sem perguntar. Setor
  "Sem Setor Principal" ou errado: `pares TICKER --setor "..."`.
- Confira se números do relatório gerencial/release batem com os informes
  oficiais (resultado distribuído, VP/cota, dívida, lucro). Divergência é
  ponto de atenção, com os dois números e as fontes.

## Comparação entre períodos

Quando o pedido é comparar relatórios ("compara os últimos 3 trimestres da
X", "o que mudou nos últimos relatórios do FII Y"), siga este roteiro em vez
do fluxo padrão de documentos (os passos 1, 2 e 5 continuam valendo):

1. **Números**: `cvm_cia.py resumo TICKER --trimestres N+1` (ou
   `cvm_fii.py trimestral FII --trimestres N+1` / `mensal`). O período extra
   mostra se a variação é tendência ou sazonalidade; a/a já vem na tabela.
2. **Documentos**: `documentos.py cia TICKER --tipo release -n N --baixar N`
   (FII: `--tipo relatorio`; relatório gerencial costuma ser mensal, então
   "últimos 3" são meses). Confira na listagem que há exatamente 1 por
   período. Se um período faltar, diga isso em vez de preencher.
3. **Mapa conjunto**: `pdf_texto.py A.pdf B.pdf C.pdf --mapa --perfil cia|fii`
   (do mais recente para o mais antigo). Casar seções **pelo título**, não
   pelo número da página: a mesma seção muda de página entre relatórios.
4. **Mesmas seções em todos**: leia as mesmas seções nos N arquivos, no
   mínimo mensagem da administração/gestão, reconciliação do EBITDA
   ajustado (ou resultado e distribuição no FII), endividamento, capex ou
   carteira, e guidance. Uma seção que existia e sumiu é informação.
5. **Busca conjunta**: `pdf_texto.py A.pdf B.pdf C.pdf --buscar "<termos>"`
   com os termos do checklist relevantes. Use a tabela termo x arquivo para
   ver o que apareceu ou sumiu, e abra só as linhas que mudaram.

Na resposta, use o formato padrão com os blocos extras de comparação
definidos em `references/formato-resposta.md` (seção "Comparação entre
períodos"). Conteúdo desses blocos:

- **Tabela lado a lado** dos N períodos (números da CVM + os do release que
  a CVM não tem, identificando a fonte de cada um).
- **O que mudou no discurso**: temas novos, temas que sumiram, mudança de
  tom sobre guidance, demanda, custos, crédito etc.
- **Promessa x entrega**: o que foi dito num período e o que aconteceu no
  seguinte (guidance, prazos de obras/emissões, desalavancagem, vacância
  prevista).
- **Ajustes recorrentes**: itens "não recorrentes" que aparecem em vários
  períodos (na prática, recorrentes).
- **Coerência release x CVM** em cada período.

## Formato da resposta

Análise completa: siga **exatamente** `references/formato-resposta.md` —
estrutura e ordem fixas, tabela de indicadores com linhas obrigatórias por
tipo de ativo (FII tijolo/papel/FoF/híbrido, empresa, banco/seguradora),
`n/d` em vez de remover linha, "Promessa × entrega" em tabela com
avaliação ✅/≈/⚠️/❌, blocos de coerência × CVM e fatos relevantes, e
nenhum comentário sobre a skill ou o processo na resposta. Leia esse
arquivo antes de escrever a resposta (junto com o checklist no passo 4).

- Cada número cita fonte e data de referência; diga quando é **calculado**
  por você/script x **informado** pela empresa/gestora.
- Tendência > número isolado: sempre que possível 8 trimestres / 12–24 meses.
- Seja específico nos alertas (ex.: "distribuiu 112% do resultado caixa no
  1T26, consumindo reserva" em vez de "atenção ao payout").
- Pergunta pontual não usa o modelo: resposta direta, com fonte e data.

## Regras

- Dados financeiros do usuário (posição, preço médio, quantidade) só se ele
  fornecer; não grave em arquivos versionados. Se pedir para salvar a
  análise, use `.cache/analise-fii-acoes/analises/` (fora do git), salvo
  instrução diferente.
- Não logue nem mostre o token; se a brapi falhar por autenticação, peça
  para o usuário conferir `BRAPI_TOKEN` no `.env` — não tente ler o arquivo.
- FundosNET não é API oficial e oscila (respostas de 0,1 s a 60 s): se
  `documentos.py fii` falhar, diga isso e siga com os dados da CVM; não fique
  repetindo em loop.
- Esta skill não altera o app (`src/`, banco). Levar cotação/fundamentos
  para o dashboard é funcionalidade nova → fluxo SDD (`nova-spec`).
