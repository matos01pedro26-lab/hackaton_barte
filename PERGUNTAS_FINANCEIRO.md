# Perguntas para o financeiro (canal `#tarvo-financeiro`)

Duas mensagens de três perguntas, no formato `[financeiro][T-800]`. Cada pergunta traz um exemplo que existe nos dados e uma resposta curta possível, para a Helena responder em uma linha. Os números foram conferidos em `data/` e no `analise_setembro.ipynb`.

As outras duas mensagens que o time tinha redigido (quem arca quando a contraparte cobra diferente, Pix à Atlas, valor da devolução à Casa) **já foram respondidas no canal** e saíram; as respostas estão na tabela abaixo e no `HIPOTESES.md` (R27 a R31).

Horário de atendimento: hoje, 9h30 às 17h30.

---

## Mensagem 1 · caixa e contas

```
[financeiro][T-800]: três perguntas sobre caixa e contas, com exemplo.

1. Regra do repasse. A senhora disse que repassa perto do dia 10 e do dia 24 "o que a Orbe já liquidou até ali". No extrato do Aurora, em 08 a 10/09 saíram R$ 2.107.818,71 de repasses (22 PIX) com R$ 1.039.172,54 recebidos da Orbe no mês até 10/09; e em 22 a 24/09, R$ 4.230.267,61 acumulados contra R$ 2.832.520,79. A diferença foi paga pela conta garantida. "Liquidou" é o que consta na agenda da Orbe, e não o TED que cai no banco? Podemos ter o extrato de repasse que a Tarvo manda aos lojistas, para conferir o valor de cada PIX? Ex.: a Mundo Aberto recebeu R$ 137.460,64 em 2 PIX, contra R$ 535.917 de líquido de vendas no relatório do mês.

2. Juros da conta garantida. O Aurora ficou negativo em 16 dos 22 dias com lançamento, chegando a −R$ 2.289.532,94 em 24/09, e o extrato de setembro não mostra juros nem IOF dessa conta (só R$ 576,50 de tarifas de pacote e de TED/PIX). Os juros são cobrados no mês seguinte? Entram em 4.3.02 (juros e multas)? E o "IOF s/ operação de crédito" de R$ 48,21 no Meridiano (FITID MRD2026090586, 26/09) é dessa conta garantida?

3. IOF das remessas. Cada TED para a Ponte é a soma de Valor R$ + IOF das operações do dia. Ex.: 01/09, R$ 240.619,49 para 11 operações. O IOF das 232 operações do mês soma R$ 21.242,79. Tratamos como repasse (baixa de "recursos de lojistas para remessas a liquidar", 2.1.02.001) e não como despesa nossa (4.3.01). Está certo, ou a Tarvo arca com parte desse IOF?
```

## Mensagem 2 · nota e cadastro

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
| Quem arca quando a contraparte cobra diferente (Bridge, Mundo Aberto, Rota Global)? | O contrato decide, não o aviso: contestar a Orbe ou a Ponte e ressarcir o lojista. Só a Casa, concessão do comercial fora do contrato, é devolução nossa (resposta ao Theo Garcia, 11h37). |
| Pix à Atlas antes de haver contrato | Sem contrato não fatura e vira pendência, mas o repasse segue normal (resposta à Southlands). |
| Valor da devolução à Casa | "O que foi cobrado eu devolvo": R$ 15.396,77, separado das divergências (respostas à Southlands e à Prime). |
| Alerta de antecipação (Atlas) | O critério é nosso, escrito no `HIPOTESES.md` (R32). |
| Spread negativo: que valor na pendência | Os dois, rotulados (resposta ao Theo Garcia). |
| Como o ajuste da Ponte aparece e entra na nota | Linha nova "AJUSTE REF PC-…", abate a participação do mês, dentro da nota única (resposta à Desbravadores, 11h33). |

---

## Conferência dos números citados

| Número | Onde está nos dados | Confere |
|---|---|---|
| Repasses: R$ 2.107.818,71 (ciclo 1) e R$ 4.230.267,61 (acumulado); TEDs R$ 1.039.172,54 e R$ 2.832.520,79 | `fato_banco` | Sim |
| Mundo Aberto: R$ 137.460,64 em 2 PIX (L26, L76); R$ 535.917 de líquido | `fato_banco` e `fato_orbe` | Sim |
| Aurora: −R$ 2.289.532,94 em 24/09; 16 de 22 dias negativos; tarifas R$ 576,50 | `fato_banco` | Sim |
| IOF das remessas R$ 21.242,79; TED de 01/09 = R$ 240.619,49 (11 operações) | `fato_ponte`, `fato_banco` | Sim |
| IOF s/ crédito R$ 48,21 (MRD2026090586); ISS R$ 21.877,40 (10/09) | `fato_banco` | Sim |
| Nota de remessa R$ 39.543,45 | notebook, seção 1.2 | Sim |
