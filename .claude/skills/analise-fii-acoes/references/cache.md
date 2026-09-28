# Cache local — organização, validade e limitações

Tudo fica em `.cache/analise-fii-acoes/` na raiz do repo (ignorado pelo git;
outro local via variável `ANALISE_CACHE_DIR`). Apagar a pasta é seguro: os
dados são baixados de novo na próxima consulta.

## Organização

A pasta segue a unidade natural de cada dado; só os PDFs são organizados por
ticker, porque são os arquivos abertos pelo caminho.

| Pasta | Chave | Motivo |
| --- | --- | --- |
| `cvm/fii/`, `cvm/cia/` (ZIPs e CSVs) | ano | Cada ZIP da CVM traz **todos** os fundos/empresas do ano; é compartilhado entre ativos (baixar por ticker duplicaria ~20 MB por ativo). |
| `cvm/cia/empresas/<CNPJ>/` | CNPJ | Linhas já filtradas de uma empresa. CNPJ e não ticker: PETR3/PETR4 (ou TAEE11/TAEE3/TAEE4) são a mesma empresa. |
| `fnet/` | CNPJ do fundo + página | Páginas da busca do FundosNET. |
| `fnet/xml/` | id do documento | Avisos de rendimento; o id é único no FundosNET. |
| `brapi/` | hash de tickers + parâmetros | Respostas de cotação; `plano.json` guarda os limites do plano (global). |
| `docs/<TICKER>/` | ticker | PDFs baixados (relatórios, releases, fatos relevantes). |
| `imagens/` | nome do PDF de origem (data, tipo, id) | Páginas renderizadas por `pdf_texto.py --imagem`. |
| `analises/` | — | Análises salvas, só quando o usuário pede. |

Analisar um ticker depois de outro não gera conflito: todas as chaves são
únicas, e o segundo ativo reaproveita os ZIPs da CVM já baixados. Efeito
colateral inofensivo: tickers da mesma empresa (PETR3 e PETR4) baixam o
mesmo documento em duas pastas de `docs/`.

## Quando um arquivo é baixado de novo

A decisão é **só pela idade do arquivo local** (data de modificação); não há
consulta à fonte para saber se o arquivo mudou. Ao precisar de um arquivo,
o script:

1. usa o do cache se ele existe e está dentro da validade;
2. baixa de novo (sobrescreve) se não existe ou venceu;
3. se o download falhar, usa a cópia antiga (com aviso), se houver.

O download é sob demanda: um arquivo vencido só é baixado de novo quando
alguma análise precisa dele.

| Arquivo | Validade | Motivo |
| --- | --- | --- |
| ZIPs da CVM do ano corrente e do anterior (informes de FII, ITR, DFP, FCA, IPE) | 24 h | A CVM atualiza diariamente; o ano anterior ainda muda (DFP publicada no ano seguinte, reapresentações). |
| ZIPs da CVM de anos mais antigos | 30 dias | Quase não mudam. |
| Cadastro de companhias (`cad_cia_aberta.csv`) | 7 dias | Muda pouco. |
| Extração por empresa (`empresas/<CNPJ>/`) | até o ZIP de origem ser rebaixado | Refeita automaticamente; mudança de formato invalida via `CACHE_VERSION` em `cvm_cia.py`. |
| Cotações (brapi) | 15 min (`--max-idade`) | Atraso da própria cotação gratuita. |
| Limites do plano (`brapi/plano.json`) | 7 dias | Ignorado quando `BRAPI_PLANO` declara um plano conhecido. |
| Buscas no FundosNET | 30 min | Pega documento novo no mesmo dia. |
| Avisos de rendimento (XML) e PDFs | sem expiração | Documento publicado não muda; reapresentação tem id novo. |

Consequências:

- Informe publicado pela CVM depois do último download só aparece quando o
  ZIP vencer (até 24 h). Como os informes saem com semanas de defasagem,
  raramente importa.
- Depois de 24 h o ZIP é baixado de novo mesmo que não tenha mudado
  (desperdício de banda, não de resultado).
- Para forçar a atualização hoje, apague o arquivo correspondente em
  `.cache/analise-fii-acoes/cvm/...` (ou a pasta inteira).

## Limitação: execuções em paralelo

Os scripts **não são seguros para duas execuções simultâneas** que baixem o
mesmo arquivo. O download grava num arquivo temporário de nome fixo
(`<arquivo>.tmp`) e depois o renomeia; dois processos baixando o mesmo ZIP
ao mesmo tempo escrevem no mesmo `.tmp` e o resultado pode sair corrompido.
Os JSONs de cache também são gravados sem trava.

Rodando uma análise de cada vez (o uso previsto: local, usuário único), não
acontece. Não dispare análises em paralelo (ex.: vários pares em processos
simultâneos) sem antes corrigir isso.

## Melhorias conhecidas (não implementadas)

- **Escrita segura para execução paralela**: arquivo temporário com nome
  único por processo (ex.: `tempfile` no mesmo diretório) + `os.replace`,
  também nos JSONs. Necessária antes de qualquer execução em paralelo.
- **Download condicional**: enviar `If-Modified-Since` / comparar o
  `Last-Modified` do servidor da CVM antes de baixar; só rebaixar quando
  houver versão nova, permitindo validade menor que 24 h sem custo de banda.
- **Opção `--atualizar`** nos scripts para forçar o download, sem apagar
  arquivos à mão.
