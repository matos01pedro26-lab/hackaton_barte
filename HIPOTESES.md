# Hipóteses, regras e perguntas — fechamento Tarvo set/2026

Este arquivo separa três coisas: o que o financeiro **confirmou**, o que eu **assumi** para seguir, e o que ainda está **em aberto**. Cada item de premissa diz o que muda se estiver errado.

---

## 1. Regras confirmadas pelo financeiro

Fonte: respostas do @manuel.freitas no canal `#tarvo-financeiro` (texto colado pelo time, sem data). A P9 cita respostas atribuídas à Helena (financeiro), conforme o arquivo do Gabriel.

| # | Regra | Efeito no cálculo |
|---|---|---|
| R1 | **Checkout é faturado pela taxa contratada**: `valor bruto × taxa da planilha`, não pelo valor cobrado pela Orbe. | A comissão sai da planilha. A Orbe vira base de comparação para as divergências. |
| R2 | **Estorno de mês anterior abate a comissão do mês do estorno**, usando a taxa válida na **data da venda original**. | O estorno entra com sinal negativo no mês dele, pela taxa da data da venda. |
| R3 | **Atlas (EC 1076801732) não é faturada** até confirmação do comercial. | Fora da comissão e da nota. |
| R4 | **Checkout: uma nota por lojista por mês.** | Um total por lojista, não por transação. |
| R5 | **Remessa: Ponte Câmbio é a tomadora única**, pelo total da participação. | Uma nota só, para a Ponte. |
| R6 | **Comissão de remessa = 50% do spread realizado.** | Já estava no e-mail da Ponte; confirmado. |
| R7 | **Spread negativo fica fora da comissão e da nota.** | 4 operações excluídas. |
| R8 | **Arredondamento comum (meio para cima), por operação.** | Vale para comissões calculadas por nós. Não corrige o truncamento da Orbe. |
| R9 | **Plano de contas registra a contrapartida** dos movimentos bancários. | Cada classificação de extrato precisa do lado oposto (partida dobrada). |
| R10 | **Divergências de remessa viram pendência de contestação com a Ponte.** | Prazo de resposta: 5 dias úteis (e-mail de 02/10 — já passou). |
| R11 | **Entrega: um repositório por time, até 18h30**, com links de plataformas no README. | Estrutura do repositório. |

---

## 2. Premissas que eu assumi

Estas não estão confirmadas. Se alguma estiver errada, o número muda na direção indicada.

| # | Premissa | Por quê | Se estiver errada |
|---|---|---|---|
| P1 | **Antecipação entra na comissão** pela taxa da planilha (2,10%). | A planilha tem a coluna; o brief diz que a Tarvo ganha a taxa de antecipação. | Comissão de checkout muda pelo total de antecipações (R$ 21 mil nos lojistas mapeados). |
| P2 | **Diferença de até R$ 0,01 entre Orbe e contrato é arredondamento**, não divergência. | A Orbe trunca em centavos (reproduz 1.943 de 1.943 linhas); o contrato arredonda. | Se a Orbe devesse arredondar, haveria ±R$ 0,01 em centenas de linhas. |
| P3 | **Vigência usa a data do movimento** nas vendas, e a **data da venda original** nos estornos. | R2 diz isso só para estornos. | Afeta a Bridge (muda em 15/09). Na prévia, 5 vendas de 15–17/09 aparecem a 2,59% em vez de 2,19%. |
| P4 | **Estabelecimento sem mapeamento confirmado fica fora da comissão**, em grupo próprio. | Casar por nome é proibido pelo brief. | Os ECs sem mapeamento somam 233 linhas e R$ 838 mil de bruto. Não entram no total. |
| P5 | **Remessa usa o spread realizado** (o que a Ponte pagou), não o da planilha. | R6 fala em "spread realizado". | O Mundo Aberto (1,50% realizado contra 1,20% na planilha) muda R$ 710 de comissão (50% de R$ 1.419 de spread). |
| P6 | **Operação "APROVADO C/ RESSALVA" entra na comissão e na nota.** | Manuel: "seguem normalmente para liquidação". | 16 operações, spread R$ 4.829,37. |
| P7 | **Operação repetida na Ponte conta uma vez.** `PC-0926-0162` aparece duas vezes, a segunda marcada "reprocessada". | Mesmos campos, mesmo valor e data. **O banco confirma**: os 21 TEDs para a Ponte somam, ao centavo, as 232 operações únicas (Valor R$ + IOF), então a cópia não foi paga. | O Resumo soma R$ 821,88 a mais. |
| P8 | **Spread "padrão" da planilha = 1,50%.** | Canguru, Kiwi e Ponte Aérea têm mediana de 1,50% realizado e spread em branco. | Só afeta a conferência, não a comissão (a comissão usa o realizado — P5). |
| P9 | **Linha do relatório da Ponte que não é operação de câmbio (ex.: crédito ou débito de ajuste) vira pendência**, fora da comissão e da nota. | O formato do ajuste não está nos dados de setembro; tratar como operação normal poderia faturar um valor errado. | Se o formato for conhecido e a regra clara, vira lançamento e deixa de ser pendência. |

### Detalhe da P9 (contribuição do Gabriel, commit `90d0d6b`; era a "P1" do arquivo dele)

- **Status:** premissa (não confirmada).
- **Contexto:** a Helena disse que a Ponte comunica o resultado de uma contestação por e-mail e envia o ajuste no relatório do mês seguinte, como crédito ou débito, e que ela registra o ajuste no fechamento do mês em que ele aparece. O relatório de setembro não tem nenhuma linha assim, então o formato dessas linhas é desconhecido.
- **Decisão:** no fechamento de outubro, qualquer linha do relatório da Ponte que não seja uma operação de câmbio normal (por exemplo, crédito ou débito de ajuste) não entra na comissão nem na nota. Ela vira pendência em `pendencias.csv`, com valor e motivo, para a Helena decidir.
- **Por quê:** o formato do ajuste não está nos dados. Tratar uma linha desconhecida como operação normal poderia faturar um valor errado. Parar e pedir decisão é a opção mais segura, e a Helena já pediu pendência para o que foge da regra.
- **Origem:** resposta 6 à pergunta da Turma do Barulho (canal #tarvo-financeiro, 17/10).
- **Relação com R10:** a contestação de divergências de remessa com a Ponte (R10) é o que gera esses ajustes no mês seguinte.

---

## 3. Perguntas em aberto para o financeiro

Ordenadas por impacto no número. Antes de perguntar, confirme se a resposta já não está no canal.

1. **Mapeamento dos ECs sem nome ou faltando na planilha.** O Manuel respondeu que mapeou, mas a lista não veio no texto colado. Preciso dela para os ECs **1038867654 (Kiwi)**, **1043300981 (Horizonte Intercâmbio / Novo Horizonte)** e **1043396662 (Horizonte Viagens)**. Os três somam 233 linhas e são o maior volume sem faturamento.
2. **Rota Global (EC 1074504011)**: desde 12/09, todas as 87 linhas de crédito saem com +0,50 p.p. sobre o contrato (prévia: R$ 1.644,28 de vendas, −R$ 98,42 de estornos). É erro da Orbe ou condição nova? Se for erro, o valor vira devolução ao lojista ou só contestação?
3. **Bridge**: confirme que a vigência das vendas segue a data do movimento (P3). Hoje, 5 vendas de 15–17/09 saem a 2,59% em vez de 2,19% (prévia: R$ 29,94).
4. **Mundo Aberto**: 1,20% (planilha, "spread negociado em jul/26") ou 1,50% (Ponte, 23 operações)? Se a planilha estiver certa, é contestação com a Ponte (R10). Se a Ponte estiver certa, a planilha está desatualizada.
5. **Atlas (EC 1076801732)**: a Aurora pagou R$ 249.301,77 em 2 PIX para a Atlas em setembro, e não há faturamento (R3). É adiantamento, pagamento de outro serviço ou erro? Qual o contrato?
6. **Spreads negativos (4 operações, R$ −1.834,05)**: a observação diz "taxa travada no pedido (D-1)". Quem absorve o prejuízo — Tarvo ou Ponte? É caso de contestação (R10) ou aceite?
7. **Saída de R$ 300.000 da Aurora em 30/09** (L92) para o Meridiano: não aparece no OFX. Está em trânsito? Entra em outubro?
8. **Aurora negativa desde 09/09** (chega a −R$ 2,29 mi). Há cheque especial autorizado, ou faltam entradas no extrato?
9. **Estornos de vendas de agosto** (9 linhas na Orbe, sem origem em setembro): a comissão deles é do mês do estorno (R2), mas a taxa de origem está nas linhas de agosto, que não temos. Confirmar que a taxa vem da planilha vigente em agosto, ou pedir o relatório de agosto.
10. **Divergências de taxa da Orbe**: o lojista pode ser cobrado a mais? Se sim, quem devolve (Tarvo ou Orbe)?

---

## 4. Achados que mudam número

Números da prévia v2 (notebook `exploracao_inicial.ipynb`, seção 10). São prévias: dependem das premissas acima e não passaram pelo financeiro.

- **Checkout (mapeados)**: R$ 194.943,54 de comissão em 18 lojistas (MDR + antecipação), com 1.653 linhas.
- **Divergências reais de taxa**: 92 linhas, soma R$ 1.575,80 cobrados a mais pela Orbe. Quase tudo é Rota Global (R$ 1.545,86 líquidos) e Bridge (R$ 29,94).
- **Arredondamento**: 1.561 linhas batem dentro de R$ 0,01 e ficam fora das divergências (P2).
- **Remessa**: comissão de R$ 39.543,45 para a nota única da Ponte, com 4 spreads negativos fora (R7) e a duplicata contada uma vez (P7).
- **Ponte — contestação**: só o Mundo Aberto tem spread realizado diferente do contratado.
- **Atlas**: 57 linhas de checkout retidas (R3). Mas a Aurora já pagou R$ 249 mil, então há pagamento sem nota.
- **Nome do lojista na nota de remessa vs checkout**: o Novo Horizonte tem CNPJ mapeado na remessa (66.564.512/0001-99), mas seu EC de checkout (1043300981) não tem mapeamento. Mesma entidade, dois status diferentes.

- **Remessa fecha com o banco**: cada um dos 21 TEDs para a Ponte é a soma de (Valor R$ + IOF) das operações do mesmo dia, e o PIX de cada lojista no Meridiano é a soma das suas operações (13 de 14 lojistas exatos). A exceção é um PIX **redondo de R$ 18.240,00** da Ponte Aérea em 17/09, sem operação correspondente: pendência.
- **Checkout não fecha com o banco**: os TEDs da Orbe (R$ 3.557.246,29) não seguem nenhuma regra simples do relatório. Os repasses a lojistas (R$ 4.230.267,61) superam os TEDs em R$ 673.021,32. Falta a regra de liquidação da Orbe (nova pergunta ao financeiro).

---

## 5. Decisões de arquitetura

- **Dados como vêm**: nada é corrigido na origem. Limpeza só em colunas derivadas.
- **Sem banco transacional**: processamento em lote. Atomicidade por publicação em `saida/` só depois das validações. Ver [notebook, seção 2](exploracao_inicial.ipynb).
- **IA só onde há ambiguidade**: classificação de lançamentos sem padrão claro e sugestão de lojista por nome (sempre com confiança baixa e revisão humana). Números vêm sempre do código, com rastro.
- **Versionamento**: um commit por versão, pela skill `commit-versao`.
