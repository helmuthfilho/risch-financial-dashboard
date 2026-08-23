---
título: Constituição do Projeto
versão: 0.3.0
atualizado_em: 2026-08-22
---

# Constituição — Dashboard Financeiro Pessoal

Este documento define os princípios não-negociáveis do projeto. Toda spec e todo
plano técnico devem estar em conformidade com ele. Mudar algo aqui é uma decisão
consciente (bump de versão + justificativa), não um ajuste incidental.

## 1. Propósito

Uma aplicação para consolidar e gerenciar o portfólio financeiro pessoal do
usuário: renda variável (ações, FIIs, ETFs, cripto), renda fixa (CDB, Tesouro,
LCI/LCA etc.) e fluxo de caixa do dia a dia (cartão de crédito, PIX, gastos
categorizados).

## 2. Princípios

1. **Dinheiro nunca é float.** Valores monetários são armazenados e somados
   como **inteiro em centavos** (`bigint`) em todas as camadas — nunca
   `float`/`double`, nunca `Decimal`/`numeric`. Campos que guardam dinheiro
   terminam em `Cents` (ex.: `amountCents`). Conversão para/de reais é
   centralizada em `src/lib/currency.ts`, nunca feita ad-hoc multiplicando/
   dividindo um `float` por 100. Ver [[0003-dinheiro-como-inteiro-em-centavos]]
   para a decisão completa e o porquê.
2. **Dados financeiros são sensíveis por padrão.** Nenhum dado de conta, saldo,
   posição ou transação é logado em texto claro, enviado a serviços de terceiros
   sem necessidade explícita, ou commitado em arquivos versionados (specs/exemplos
   usam dados fictícios).
3. **Fonte da verdade auditável.** Toda alteração de saldo/posição deve ser
   rastreável a uma transação ou evento importado — sem edição silenciosa de
   totais agregados.
4. **Local-first / usuário único (por enquanto).** A aplicação é para uso
   pessoal do usuário. Multi-usuário, autenticação de terceiros e
   compartilhamento são fora de escopo até decisão explícita em contrário.
5. **Specs antes de código para funcionalidade nova.** Qualquer funcionalidade
   não-trivial (nova tela, novo tipo de ativo, nova integração, mudança de
   modelo de dados) passa pelo fluxo Spec → Plano → Tasks → Implementação
   descrito em [[workflow]]. Correções pontuais e ajustes triviais podem pular
   direto para implementação.
6. **Simplicidade primeiro.** Preferir a solução mais simples que resolve o
   problema atual. Abstrações e integrações "para o futuro" exigem justificativa
   explícita no plano técnico.
7. **Nomenclatura em português para domínio, inglês para código.** Termos de
   negócio (specs, glossário, conversas) em PT-BR; identificadores de código
   (variáveis, funções, tabelas) em inglês, para manter consistência com o
   ecossistema técnico.
8. **Lógica de negócio pura sempre tem teste unitário.** Utilitários,
   validação e cálculos (`src/lib/**`, exceto infraestrutura trivial) são
   testados na mesma task em que são escritos, com coverage mínimo de 80%
   reforçado por `npm run test:coverage`. Componentes React, páginas e
   Server Actions não entram nesse escopo — continuam validados via o
   driver de navegador da skill `run-risch-financial-dashboard`. Ver
   [[0004-testes-unitarios-obrigatorios-para-logica-de-negocio]].

## 3. Fora de escopo (até decisão em contrário)

- Multi-usuário / multi-tenant.
- Execução de ordens (compra/venda real) — a aplicação é de acompanhamento,
  não de corretagem.
- Conexão automática via Open Finance/screen scraping com bancos — entra apenas
  se e quando houver uma spec dedicada avaliando segurança e custo.

## 4. Como este documento é usado

- Toda spec em `docs/specs/` deve citar explicitamente quaisquer princípios
  relevantes que ela toca ou tensiona.
- Se uma spec violar um princípio, isso deve ser justificado na seção
  "Desvios da constituição" da própria spec, não ignorado silenciosamente.

Ver também: [[glossary]], [[workflow]].
