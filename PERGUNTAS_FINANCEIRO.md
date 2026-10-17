# Perguntas para o financeiro (canal `#tarvo-financeiro`)

Quatro mensagens de três perguntas, no formato `[financeiro][T-800]`. Cada pergunta traz um exemplo que existe nos dados e uma resposta curta possível, para a Helena responder em uma linha. Os números foram conferidos em `data/` e no `analise_setembro.ipynb` (tabela no fim).

Horário de atendimento: hoje, 9h30 às 17h30.

---

## Mensagem 1 (rascunho do time; só ajustei uma frase para ficar fiel ao que a Helena disse sobre a Casa)

```
[financeiro][T-800]: três perguntas de regra, com exemplo.

1. Quando a contraparte não foi avisada. Na Casa a senhora disse que ninguém avisou a Orbe, então ela cobrou, e que o cobrado a senhora devolve ao lojista. Dois casos ficam no meio:
(a) Bridge: a planilha já dizia 2,19% a partir de 15/09, mas a Orbe só foi avisada dias depois e cobrou 2,59% em 5 vendas de 15 a 18/09 (R$ 29,95, ex.: TX88428053).
(b) Mundo Aberto: o spread de 1,20% está na planilha desde julho, mas a Ponte nunca foi avisada (23 operações, R$ 1.418,85, ex.: PC-0926-0016).
O que decide se cobramos da contraparte: (i) a condição estar na planilha, mesmo sem aviso, e aí Bridge e Mundo Aberto seguem como cobrança da Orbe e contestação com a Ponte; ou (ii) a contraparte ter sido avisada, e aí os dois viram devolução nossa ao lojista, como a Casa?

2. Alerta de antecipação. Na Atlas o alerta é claro: ela antecipou R$ 179.592,82 em 15/09 com R$ 55.357,50 vendidos desde que começou, em 10/09. Mas pela regra "antecipou mais do que vendeu no mês", outros 5 lojistas também acenderiam. Por exemplo, a Canguru antecipou R$ 31.765,12 em 01/09 com R$ 1.934,10 vendidos no mês, provavelmente sobre parcelas de vendas de agosto que o relatório não traz. Alertamos só quem não tem vendas antes do mês (em setembro, só a Atlas), ou existe outro limite que a senhora usa?

3. Spread negativo. Na pendência de contestação com a Ponte, o valor de cada operação é o spread negativo do relatório (ex.: PC-0926-0210, −R$ 687,52) ou a diferença até o spread do contrato (1,5% sobre a PTAX, −R$ 1.351,87)?
```

---

## Mensagem 2 · valores e quem arca

```
[financeiro][T-800]: três perguntas sobre valores e quem arca, com exemplo.

1. Rota Global. A senhora disse que o contrato da Rota não mudou este ano. Desde 12/09 a Orbe cobrou +0,50 p.p. em todo crédito (87 linhas, R$ 1.546,28 por bruto × diferença da taxa). Ex.: TX88423890, de 12/09, R$ 6.449,10 em 7 a 12x, cobrado a 4,09% em vez de 3,59%: R$ 32,25. Diferente da Casa, aqui não há aviso que a Orbe tenha deixado de receber. A pendência é: (i) devolver ao lojista e cobrar a Orbe; ou (ii) só devolver ao lojista, como na Casa?

2. Atlas, repasses antes do contrato. O Aurora pagou à Atlas R$ 249.301,77 em dois PIX: L34, em 10/09, R$ 112.220,15, no mesmo dia em que ela começou a transacionar; e L60, em 22/09, R$ 137.081,62. Não há contrato assinado na planilha vigente. Esses repasses foram autorizados pelo comercial? Lançamos como repasse a lojista (2.1.01.001) e abrimos pendência de aprovação para a senhora, ou eles têm outro tratamento?

3. Valor da devolução à Casa. O cobrado pela Orbe em vendas e antecipações de setembro da Casa é R$ 15.396,77 (R$ 12.578,29 de vendas e R$ 2.827,56 de antecipações, menos R$ 9,08 do estorno de 29/09). Pela sua regra de divergência (bruto × taxa), o valor seria R$ 15.397,42; a diferença de R$ 0,65 vem do truncamento da Orbe. A devolução ao lojista é (i) o que a Orbe cobrou, R$ 15.396,77; ou (ii) o da divergência, R$ 15.397,42?
```

## Mensagem 3 · caixa e contas

```
[financeiro][T-800]: três perguntas sobre caixa e contas, com exemplo.

1. Regra do repasse. A senhora disse que repassa perto do dia 10 e do dia 24 "o que a Orbe já liquidou até ali". No extrato do Aurora, em 08 a 10/09 saíram R$ 2.107.818,71 de repasses (22 PIX) com R$ 1.039.172,54 recebidos da Orbe no mês até 10/09; e em 22 a 24/09, R$ 4.230.267,61 acumulados contra R$ 2.832.520,79. A diferença foi paga pela conta garantida. "Liquidou" é o que consta na agenda da Orbe, e não o TED que cai no banco? Podemos ter o extrato de repasse que a Tarvo manda aos lojistas, para conferir o valor de cada PIX? Ex.: a Mundo Aberto recebeu R$ 137.460,64 em 2 PIX, contra R$ 535.917 de líquido de vendas no relatório do mês.

2. Juros da conta garantida. O Aurora ficou negativo em 16 dos 22 dias com lançamento, chegando a −R$ 2.289.532,94 em 24/09, e o extrato de setembro não mostra juros nem IOF dessa conta (só R$ 576,50 de tarifas de pacote e de TED/PIX). Os juros são cobrados no mês seguinte? Entram em 4.3.02 (juros e multas)? E o "IOF s/ operação de crédito" de R$ 48,21 no Meridiano (FITID MRD2026090586, 26/09) é dessa conta garantida?

3. IOF das remessas. Cada TED para a Ponte é a soma de Valor R$ + IOF das operações do dia. Ex.: 01/09, R$ 240.619,49 para 11 operações. O IOF das 232 operações do mês soma R$ 21.242,79. Tratamos como repasse (baixa de "recursos de lojistas para remessas a liquidar", 2.1.02.001) e não como despesa nossa (4.3.01). Está certo, ou a Tarvo arca com parte desse IOF?
```

## Mensagem 4 · nota e cadastro

```
[financeiro][T-800]: três perguntas sobre a nota e o cadastro, com exemplo.

1. Razão social na nota. A planilha tem nomes curtos (ex.: "Vela", "Canguru", "Mundo Aberto", "EduAbroad"), enquanto a Orbe e a Ponte escrevem outros ("VELA TURISMO EDUCACIONAL", "MUNDO ABERTO INTERC LTDA"). A nota de checkout precisa da razão social do tomador. De onde tiramos: do ERP, do contrato de adesão? Enquanto isso, podemos usar o nome da planilha junto com o CNPJ e marcar "a conferir"?

2. CNPJ com 13 dígitos. A planilha perdeu o zero à esquerda de dois CNPJs: Fluente (3229837000103) e Campus Global (8780784000120). Completamos para 03229837000103 e 08780784000120. Confere?

3. Retenção na nota da Ponte. A nota de intermediação de setembro é de R$ 39.543,45. A Ponte retém ISS ou IRRF no pagamento, de modo que o repasse de 06/10 chegue menor que a nota? Hoje a Tarvo recolhe ISS pelo DAMSP no mês seguinte (R$ 21.877,40 em 10/09, de agosto). O ISS dessa nota entra no DAMSP de outubro?
```

---

## O que não precisamos perguntar (já respondido)

| Dúvida | Resposta da Helena |
|---|---|
| "A Orbe não parece cobrar nada: é erro ou ela não cobra?" | A comissão é a taxa inteira, **sem desconto de custo da Orbe**. Nada a perguntar: a Tarvo não tem custo da Orbe a abater neste modelo. |
| Estorno de venda de agosto | Entra em setembro, pela taxa da venda original. |
| Quais são os ECs sem cadastro | Os três estão mapeados; a Atlas fica retida. |
| Regra das notas, remessa e arredondamento | Ver `HIPOTESES.md`, R10 a R17. |
| Por que o Aurora fica negativo | É a conta garantida usada para repassar antes de a Orbe liquidar. |
| Os R$ 300.000, os R$ 18.240 e os R$ 12.400 | Em trânsito (cai em 01/10); remessa de outubro; PIX de repasse que voltou (motivo ainda desconhecido). |

---

## Conferência dos números citados

| Número | Onde está nos dados | Confere |
|---|---|---|
| Bridge: 5 vendas, R$ 29,95 (bruto × Δ), ex. TX88428053 | `fato_orbe`, EC 1075624862, crédito à vista a 2,59% após 15/09 | Sim |
| Mundo Aberto: 23 operações, R$ 1.418,85 | `fato_ponte`, `flag_spread_diverge`, (spread % − 1,20) × PTAX × valor ME | Sim |
| Atlas: R$ 179.592,82 em 15/09; R$ 55.357,50 vendidos até 15/09 | 4 antecipações de 15/09; vendas de 10 a 15/09 | Sim |
| Canguru: R$ 31.765,12 (AN88444882) e R$ 1.934,10 (TX88410106) em 01/09 | `fato_orbe` | Sim |
| PC-0926-0210: −R$ 687,52 e −R$ 1.351,87 | `spread_brl`; 1,5% × PTAX 6,2488 × 7.087,81 = R$ 664,35, e 664,35 + 687,52 | Sim |
| Spreads negativos: R$ 3.565,98 em 4 operações | soma das diferenças até o contrato | Sim |
| Rota Global: 87 linhas, R$ 1.546,28; TX88423890 = R$ 32,25 | 6.449,10 × 0,5% = 32,2455 | Sim |
| Atlas: PIX de R$ 112.220,15 (L34) e R$ 137.081,62 (L60) | `fato_banco` | Sim |
| Casa: R$ 15.396,77 cobrado; R$ 15.397,42 pela regra; estorno de 29/09 = −R$ 9,08 | `fato_orbe` e notebook, H4b | Sim |
| Repasses: R$ 2.107.818,71 (ciclo 1) e R$ 4.230.267,61 (acumulado); TEDs R$ 1.039.172,54 e R$ 2.832.520,79 | `fato_banco` | Sim |
| Mundo Aberto: R$ 137.460,64 em 2 PIX (L26, L76); R$ 535.917 de líquido | `fato_banco` e `fato_orbe` | Sim |
| Aurora: −R$ 2.289.532,94 em 24/09; 16 de 22 dias negativos; tarifas R$ 576,50 | `fato_banco` | Sim |
| IOF das remessas R$ 21.242,79; TED de 01/09 = R$ 240.619,49 (11 operações) | `fato_ponte`, `fato_banco` | Sim |
| IOF s/ crédito R$ 48,21 (MRD2026090586); ISS R$ 21.877,40 (10/09) | `fato_banco` | Sim |
| Nota de remessa R$ 39.543,45 | notebook, seção 1.2 | Sim |
