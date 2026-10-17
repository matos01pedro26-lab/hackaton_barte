# Hipóteses, regras e perguntas — fechamento Tarvo set/2026

Este arquivo separa três coisas: o que o financeiro **confirmou**, o que nós **assumimos** para seguir, e o que ainda está **em aberto**. Cada premissa diz o que muda se estiver errada. Cada regra diz onde ela vive nos dados.

**Fonte das regras confirmadas:** respostas no canal `#tarvo-financeiro` (16 e 17/10). As respostas aparecem postadas pelo perfil `@manuel.freitas` e assinadas "Helena, financeiro da Tarvo"; tratamos como o mesmo interlocutor. As decisões estão registradas como dado em `config/` (com quem aprovou e quando) e são lidas por `src/ingestao.py`.

**Dados de entrada:** ficam todos em `input/`. Além dos 6 arquivos base, chegou depois o `06_orbe_ajustes_tardios_set2026.csv` (14 lançamentos da Orbe de 30/09). A ingestão lê qualquer arquivo no formato da Orbe do mesmo mês e o grava em `fato_orbe` com o `arquivo_origem` e o `lote` (`BASE` ou `TARDIO`), conferindo que cada ajuste aponta para uma linha existente, de valor oposto, mesma taxa e mesmo EC.

---

## 1. Regras confirmadas pelo financeiro

### Checkout

| # | Regra | Onde vive |
|---|---|---|
| R1 | A comissão é a **taxa inteira, sem custo da Orbe**, calculada pela **taxa contratada** (bruto × taxa da planilha), não pelo `valor_taxa` da Orbe. | `dim_contrato_taxa`, `fato_orbe` |
| R2 | **Estorno devolve a taxa ao lojista e abate a comissão do mês do estorno**, mesmo de venda de agosto (agosto já está fechado e não reabre). A taxa usada é a que valia **na data da venda original**. | `fato_orbe.data_taxa_ref` |
| R3 | **Antecipação** entra na mesma nota (bruto × taxa contratada). A **reversão** só anula a taxa da antecipação que ela reverte. | `fato_orbe.faixa = antecipacao` |
| R4 | **Arredondamento comum** (meio para cima; no negativo vale a mesma regra com o sinal: −0,005 vira −0,01), **linha por linha e depois soma**. A Orbe trunca; a Tarvo não. Na remessa: por operação (50% de R$ 262,01 = R$ 131,01). | notebook, seção 1.4 |
| R5 | **Divergência de checkout** existe quando a taxa aplicada é diferente da contratada, e vale **bruto × (aplicada − contratada)**. Diferença de centavo por truncamento da Orbe **não** é divergência. | notebook, seção 1.4 |
| R6 | **Mapeamento de ECs**: 1043300981 é a Novo Horizonte Intercâmbio; 1043396662 é a Horizonte Viagens e Turismo (empresa diferente da Novo Horizonte); 1038867654 é a Kiwi Experience. CNPJ e taxas estão nas linhas delas na planilha vigente. | `config/mapeamento_ec.csv`, `dim_ec` |
| R7 | **Atlas (EC 1076801732)**: começou a transacionar em 10/09, sem contrato assinado na planilha vigente. **Não se fatura** até o comercial confirmar a taxa. Quando confirmar, a taxa vale **desde 10/09** e setembro é faturado **junto com outubro** (outubro precisa puxar as linhas da Atlas de setembro). | `config/mapeamento_ec.csv` (RETIDO) |
| R8 | **Casa do Estudante**: tarifa zerada no checkout de setembro a dezembro (MDR e antecipação), por acordo do comercial. Remessa segue normal. A Orbe não foi avisada e cobrou; **o cobrado é devolvido ao lojista**, junto com o comercial, separado das divergências de contrato (R28). | `config/condicoes_comerciais.csv` |
| R9 | **Rota Global**: o contrato não mudou este ano. A cobrança de +0,50 p.p. desde 12/09 é **divergência**. | notebook, H2 |

### Notas fiscais

| # | Regra |
|---|---|
| R10 | **Checkout**: uma nota por lojista por mês, no valor da comissão do mês pela taxa contratada. Sem texto padrão: serviço e competência bastam. **Zero ou negativo não emite nota**; o negativo **não** passa automaticamente ao mês seguinte; vira **pendência para a Helena**. |
| R11 | **Remessa**: uma nota só, com a **Ponte Câmbio** como tomadora, pelo total da participação do mês. Não há nota por lojista. |

### Remessa (Ponte Câmbio)

| # | Regra | Onde vive |
|---|---|---|
| R12 | A comissão é **50% do "Spread R$" realizado**, por operação. | notebook, seção 1.2 |
| R13 | Spread em branco ou "padrão" na planilha = **1,5% sobre a PTAX**. | `config/parametros.csv` |
| R14 | **Spread negativo** não é aceito (a trava vale 2 horas pelo contrato e essas passaram do prazo): fora da comissão e da nota, e é contestado. | `fato_ponte.flag_spread_negativo` |
| R15 | **Operação repetida**: o número da operação é único. Conta uma vez e entra na lista de correção para a Ponte. | `fato_ponte.flag_duplicata` |
| R16 | **"Aprovado c/ ressalva"** não muda nada. Vale a **data de contratação** (não a de liquidação). | `fato_ponte.mes_contratacao` |
| R17 | **Divergência de remessa** = **valor cheio**: (spread % aplicado − contratado) × PTAX × valor em moeda estrangeira. Mundo Aberto (1,20% desde julho) é divergência, contestada com a Ponte. A **nota de setembro sai pelo realizado**; a contestação é um processo à parte, e se a Ponte devolver a diferença, a nossa metade sai no mês do ajuste. A tolerância para arredondamento é critério da equipe, escrito com o motivo. | `fato_ponte.flag_spread_diverge`, `config/parametros.csv` |
| R18 | A Ponte **ainda não foi contestada**: considerar dentro do prazo. Manter **pendência de contestação com valor e operações** (inclui a duplicada). Depois, a Ponte responde por e-mail e manda o ajuste no relatório do mês seguinte, como crédito ou débito; a Helena registra no mês em que o ajuste aparece. | ver R27 |
| R19 | O **PIX de R$ 18.240,00 da Ponte Aérea** (17/09) é dinheiro de uma remessa que sai em outubro. Operação de **CNPJ fora da planilha**: calcular a nossa metade mesmo assim e abrir pendência de cadastro para o comercial (tratamento aceito como razoável). | `fato_ponte.flag_cnpj_fora_da_tabela` |

### Bancos e contabilidade

| # | Regra | Onde vive |
|---|---|---|
| R20 | O plano de contas registra a **contrapartida** do movimento no banco. Se o valor já estava registrado, o pagamento ou recebimento **baixa a conta onde estava**; não vira receita ou despesa de novo. | `dim_plano_contas` |
| R21 | **Provisionados**: folha, ISS, INSS, FGTS e DARFs (IRRF, PIS, COFINS) de agosto, e o repasse de comissão da Ponte de 04/09 (spread de agosto, já "comissão a receber"). "Todo mês a folha e os impostos do mês ficam provisionados no fechamento, e o pagamento no mês seguinte baixa a provisão." **Nada mais** estava provisionado: tarifas, aluguel, cloud, assinaturas e serviços entram direto na despesa do mês. Quando o extrato não deixa claro, declarar a premissa e seguir. | `fato_banco.provisionado_antes`, `competencia_declarada` |
| R22 | **PIX de R$ 7.350,00** sem identificação: não é receita até alguém identificar. **Devolução de R$ 12.400,00** do Mundo Aberto: é um PIX de repasse que voltou, motivo ainda desconhecido. **Transferência de R$ 300.000,00**: saiu do Aurora em 30/09 e cai no Meridiano em 01/10. O tratamento de cada um é decisão da equipe. | notebook, seção 4 |
| R23 | Devolução de PIX em `2.1.01.001` ou `2.1.01.002`: "as duas fazem sentido; escolham uma, mantenham o mesmo critério e escrevam o motivo". | P5 |
| R24 | A **Orbe deposita tudo no Aurora** e não paga lojista direto. **Débito e Pix caem no dia seguinte**; **crédito e parcelado ao longo dos meses**, conforme as parcelas. O saldo negativo do Aurora é a **conta garantida**, usada para pagar os lojistas antes de a Orbe liquidar. **Não é preciso conciliar parcela a parcela** neste fechamento: os créditos da Orbe são classificados, e o resto espera a agenda de recebíveis. | notebook, H8 a H10 |
| R25 | O repasse é feito **duas vezes por mês, perto do dia 10 e do dia 24**, "o que a Orbe já liquidou até ali". A regra está no contrato de adesão de cada lojista (pasta do comercial). | notebook, H8 |

### Governança

| # | Regra |
|---|---|
| R26 | **Taxa e condição comercial**: aprova o comercial, e a Helena registra. **Regra de como fechar**: aprova a Helena. Nas férias dela, hoje ninguém fecha. Registrar **quem aprovou e quando** (já feito em `config/`). |

### Complementos (respostas do meio-dia de 17/10, posteriores ao v6)

| # | Regra | Onde vive |
|---|---|---|
| R27 | **Ajuste da Ponte**: linha nova, com Nº de operação próprio e Spread R$ negativo; a observação traz "AJUSTE REF PC-…" (a operação original). Entra no **mês em que aparece** e **abate a nossa participação**, dentro da nota única da Ponte; o rastro aponta para a operação original. Não há nota complementar. Se o mês fechar zerado ou negativo, não emite e vira pendência. Setembro não tem nenhum. | `src/remessa/regras.py` |
| R28 | **Casa do Estudante**: a devolução ao lojista fica **separada das divergências de contrato**. O valor é o que a Orbe cobrou nas 118 linhas isentas (vendas, antecipações e o estorno de 29/09): **R$ 15.396,77**. O estorno de 21/08 (R$ 5,50) usa a taxa de agosto e não entra nesse valor. | `fato_orbe` com `data_taxa_ref` ≥ 2026-09-01 |
| R29 | **Quem arca quando a contraparte cobra diferente**: o que decide é o **contrato**, não o aviso. Bridge (aditivo de 2,19%), Mundo Aberto (1,20%) e Rota Global são divergência: contestar a Orbe ou a Ponte e ressarcir o lojista. Só a Casa, concessão do comercial fora do contrato, é devolução nossa. | R5, R9, R17 |
| R30 | **Spread negativo na pendência de contestação**: os dois valores, rotulados. O spread negativo do relatório (o que aconteceu) e a diferença até o spread do contrato (o que se pede à Ponte, porque a trava deveria ter sido honrada). | `remessa_pendencias.csv`: `SPREAD_NEGATIVO` e `CONTESTACAO_ATE_CONTRATO` |
| R31 | **Atlas**: sem contrato assinado, não fatura e vira pendência, mas o **repasse segue normal** (os Pix à Atlas não são pendência). O CNPJ da aba de 2025 (39.566.044/0001-19) pode identificá-la; a taxa daquela aba não vale. Comissão zerada com pendência, ou fora do arquivo: escolha nossa. | R7 |
| R32 | **Alerta de antecipação**: o critério é da equipe, porque a agenda inclui vendas de meses anteriores que o relatório não traz. Não há limite definido pelo financeiro. | em aberto (seção 3) |

---

## 2. Premissas que a equipe assumiu

As oito premissas antigas (antecipação na comissão, truncamento da Orbe, vigência, EC sem mapeamento, spread realizado, ressalva, duplicata e spread padrão) foram **confirmadas** pelo financeiro (R1 a R5, R6/R7, R12, R16, R15, R13). As que valem agora:

| # | Premissa | Por quê | Se estiver errada |
|---|---|---|---|
| P1 | **Tolerância de 0,005 p.p.** entre o spread aplicado e o contratado (em `config/parametros.csv`, fonte única da ingestão e do módulo de remessa). | O ruído do spread da Ponte fica em ±0,0016 p.p., sem viés por lojista; a única divergência real de setembro (Mundo Aberto) está em +0,30 p.p. 0,005 p.p. é 3 vezes o ruído e 60 vezes menor que a divergência real. Em reais não separa bem (o ruído chega a R$ 0,70 e cresce com a operação). Estudo: `notebooks/remessa_tolerancia.ipynb`. | Abaixo disso viraria alarme de centavo; acima, perderíamos diferença real. Um mês só: rever com outubro. |
| P2 | **"Setembro a dezembro"** da Casa = 01/09/2026 a 31/12/2026 (meses inteiros). | O texto não dá os dias. | Se terminar antes, a taxa volta antes. |
| P3 | **Vigência das vendas pela data da venda** (movimento). Só o estorno olha a data da venda original (R2). | R2 trata o estorno; para venda, a data do movimento é a da venda. | Afeta a Bridge (muda em 15/09). |
| P4 | A **competência** da comissão é a do mês da **contratação** (remessa) e a do mês do **movimento** (checkout, incluindo o estorno). | R2 e R16. | Mudaria o mês de 6 operações liquidadas em outubro. |
| P5 | **Devolução de PIX (R$ 12.400,00)** em `2.1.01.001` (Repasses a lojistas a pagar). | A Helena descreveu como "um PIX de repasse que voltou": o repasse volta a ser devido. | Se for devolução ao lojista, seria `2.1.01.002`. |
| P6 | **PIX de R$ 7.350,00** em `1.1.09.002` (Créditos não identificados). | "Não é receita até alguém identificar." | Se identificarem, reclassifica. |
| P7 | **PIX de R$ 18.240,00** da Ponte Aérea em `2.1.02.001` (Recursos de lojistas para remessas a liquidar). | R19: é uma remessa que sai em outubro. | Se fosse receita, seria erro de classificação. |
| P8 | **Transferência de R$ 300.000,00** de 30/09 em `1.1.09.001` (Transferências entre contas próprias). Entrada no Meridiano só em 01/10. | R22. | Sem contrapartida no mês até a entrada. |
| P9 | ~~Linha do relatório da Ponte que não é operação de câmbio vira pendência.~~ **Superada pela R27**: a Helena respondeu que o ajuste vem como linha nova (`AJUSTE REF PC-…`) e abate a participação do mês. | Hoje o formato é conhecido. | Linha que não seja operação nem ajuste reconhecível continua sendo pendência. |
| P10 | **IOF das remessas** (R$ 21.242,79) é repasse, não despesa da Tarvo: o TED para a Ponte é (Valor R$ + IOF). O **IOF s/ operação de crédito** de R$ 48,21 (Meridiano, 26/09) vai para `4.3.01`. | O banco mostra os TEDs fechando com Valor R$ + IOF. | Se parte do IOF das remessas for custo da Tarvo, mudaria o resultado. |
| P11 | **CNPJs com 13 dígitos** na planilha (Fluente, Campus Global) tiveram o zero à esquerda restaurado. | A planilha perdeu o zero (formato numérico). | Nota emitida com CNPJ errado. |
| P12 | Os **PIX à Atlas** (R$ 249.301,77 em 2 repasses) entram em `2.1.01.001` como **repasse normal**. A pendência da Atlas é de **faturamento** (R7), não dos PIX. | A Helena disse que, sem contrato, a Atlas "não fatura, vira pendência, e o repasse continua normal" (R31). | Se fosse adiantamento, `1.1.03.003`. |
| P13 | Os **ajustes tardios da Orbe** (arquivo 06, todos com `data_movimento` 30/09) entram em **setembro**, pela data do movimento. | Foram datados 30/09 e o arquivo é de set/2026. Para a Ponte a Helena disse que o ajuste entra no mês em que aparece; aqui assumimos que são lançamentos de setembro que chegaram depois do relatório. | Se valerem em outubro, a comissão de setembro sobe R$ 3.304,39 e sai da de outubro. |
| P14 | **Após 31/12/2026 a Casa do Estudante volta às taxas da planilha** (linha `TABELA (retomada)` em `dim_contrato_taxa`, vigente a partir de 2027-01-01). | A Helena só deu "setembro a dezembro". | Se a isenção continuar, a tabela precisa de uma nova condição em `config/condicoes_comerciais.csv`. |
| P15 | **Fluente Idiomas: o Pix a 0,79% da planilha é pendência**, e é um achado a destacar no case. Os demais lojistas têm 0,89%. A Orbe cobrou 0,79% nas 8 vendas de Pix da Fluente, então não há divergência entre planilha e Orbe; calculamos a comissão pela planilha como está e abrimos pendência com as 8 transações, para o comercial (quem aprova taxa) confirmar. | Parece erro de digitação na planilha, e é o tipo de erro que o fechamento manual não percebe. Decisão do grupo em 17/10. | Se o contrato real for 0,89%, a Orbe cobrou 0,10 p.p. a menos nessas 8 vendas e a comissão de Pix da Fluente está subestimada. |
| P16 | O **valor da divergência de remessa** é `Spread R$` realizado − spread contratado × Valor ME × PTAX (valor cheio), em `Decimal`, arredondado ao centavo por operação. | Usa o valor que a Ponte pagou, sem passar pelo `spread_pct` do relatório, que vem arredondado. | Pelo `spread_pct` a Mundo Aberto daria R$ 1.418,85 em vez de R$ 1.418,88 (3 centavos). |

### Detalhe da P9 (contribuição do Gabriel, commit `90d0d6b`; era a "P1" do arquivo dele) — superada pela R27, mantida como histórico

- **Status:** superada pela R27 (resposta da Helena às 11h33 de 17/10).
- **Contexto:** a Helena disse que a Ponte comunica o resultado de uma contestação por e-mail e envia o ajuste no relatório do mês seguinte, como crédito ou débito, e que ela registra o ajuste no fechamento do mês em que ele aparece. O relatório de setembro não tem nenhuma linha assim, então o formato dessas linhas é desconhecido.
- **Decisão:** no fechamento de outubro, qualquer linha do relatório da Ponte que não seja uma operação de câmbio normal (por exemplo, crédito ou débito de ajuste) não entra na comissão nem na nota. Ela vira pendência em `pendencias.csv`, com valor e motivo, para a Helena decidir.
- **Por quê:** o formato do ajuste não está nos dados. Tratar uma linha desconhecida como operação normal poderia faturar um valor errado. Parar e pedir decisão é a opção mais segura, e a Helena já pediu pendência para o que foge da regra.
- **Origem:** resposta 6 à pergunta da Turma do Barulho (canal #tarvo-financeiro, 17/10).

---

## 3. Perguntas

### Já respondidas

| Pergunta (resumo) | Resposta | Regra |
|---|---|---|
| Estorno devolve a taxa? E de venda de agosto? | Sim; entra em setembro, pela taxa da venda original | R2 |
| Quais são os ECs sem cadastro? A Atlas é ativa? | 3 mapeados; Atlas retida | R6, R7 |
| Regra das notas (checkout e remessa) | Uma nota por lojista; remessa só na Ponte | R10, R11 |
| Comissão de remessa: realizado ou contratado? | 50% do realizado; padrão 1,5% | R12, R13 |
| Spread negativo, duplicata, ressalva, data | Fora; conta uma vez; irrelevante; contratação | R14 a R16 |
| Rota Global, Casa, competência dos pagamentos | Divergência; tarifa zerada; folha e tributos provisionados | R9, R8, R21 |
| Arredondamento e divergência de remessa | Comum por linha; valor cheio | R4, R17 |
| Plano de contas: contrapartida? | Sim, baixando o que já estava registrado | R20, R21 |
| Contestação da Ponte | Ainda não aberta; pendência com valor e operações | R18 |
| Fluxo Aurora × Orbe | Conta garantida; D+1 e meses seguintes | R24 |
| A Orbe cobra algo da Tarvo? | A comissão é a taxa inteira, sem custo da Orbe | R1 |
| Quem aprova regras? | Comercial (taxa), Helena (como fechar) | R26 |
| Quem arca quando a contraparte cobra diferente (Bridge, Mundo Aberto, Rota Global)? | O contrato decide, não o aviso: contestar e ressarcir o lojista; só a Casa é devolução nossa | R29 |
| Pix à Atlas antes de haver contrato? | O repasse segue normal; só o faturamento fica suspenso | R31 |
| Valor da devolução à Casa e se entra nas divergências | O que a Orbe cobrou (R$ 15.396,77), separado das divergências | R28 |
| Como o ajuste da Ponte aparece e entra na nota? | Linha nova "AJUSTE REF PC-…", abate a participação do mês, dentro da nota única | R27 |
| Spread negativo: que valor entra na pendência? | Os dois, rotulados | R30 |

### Em aberto

Estão redigidas, com exemplo, em [PERGUNTAS_FINANCEIRO.md](PERGUNTAS_FINANCEIRO.md), em duas mensagens de três perguntas prontas para o canal. As três que o time tinha sobre Rota Global e Bridge, Pix à Atlas e valor da devolução à Casa foram respondidas no canal e saíram da lista (R28 a R31):

1. Regra do repasse ("o que a Orbe já liquidou") contra os números do extrato.
2. Juros e IOF da conta garantida.
3. IOF das remessas e o IOF de R$ 48,21.
4. Razão social para a nota (a planilha tem nomes curtos).
5. CNPJs com zero à esquerda restaurado.
6. Retenção de ISS na nota de remessa.
7. **Ajustes tardios da Orbe (arquivo 06)**: os estornos, as reversões de antecipação e a venda da Kiwi de 30/09 entram em setembro ou em outubro (P13)? Efeito: R$ 3.304,39 na comissão de checkout e nas notas.
8. **Reversões de antecipação tardias** (R$ 121.742,45, Oxford e Maple): a Orbe desconta isso dos TEDs de outubro? As antecipações originais, pagas em D+1, já estavam nos TEDs de setembro?

Decisões do grupo, que não são perguntas ao financeiro: o critério do alerta de antecipação (R32) e se a Atlas sai com comissão zerada e pendência ou fora do arquivo (R31).

---

## 4. Achados que mudam número

Números do notebook `analise_setembro.ipynb` (prévias; o financeiro disse que não valida números, quem fecha somos nós):

- **Dados tardios não trouxeram o dinheiro que faltava.** O arquivo 06 só muda o que a Orbe *reporta*: −R$ 142.565,06 no líquido (10 estornos −R$ 26.127,80, 3 reversões de antecipação −R$ 121.742,45 e uma venda da Kiwi +R$ 5.305,19). Os extratos do Aurora e do Meridiano são idênticos aos de antes. O reportado que ainda não entrou caiu de R$ 3.707.101,91 para R$ 3.564.536,85 porque a promessa diminuiu, e não porque entrou dinheiro. Os TEDs de setembro equivalem a 49,95% do reportado, mas incluem R$ 2,3 mi de parcelas de vendas de meses anteriores: do que a Orbe reportou *para setembro*, entraram só cerca de R$ 1,26 mi (débito, Pix e antecipações); o resto (R$ 5,85 mi) é crédito em parcelas.
- **Checkout** (já com os ajustes tardios, −R$ 3.304,39 na comissão): R$ 203.740,84 pela taxa contratada, em 20 lojistas com nota. **Casa do Estudante** fica com comissão de **−R$ 5,50** (só o estorno de uma venda de agosto), então **não emite nota** e vira pendência (R10).
- **Divergências de contrato de checkout** (para `divergencias_taxa.csv`): R$ 1.576,23 em 92 linhas (Rota Global R$ 1.546,28; Bridge R$ 29,95). A **Casa não entra aqui** (R28): são 118 linhas (R$ 15.397,42 por bruto × taxa) tratadas como devolução ao lojista, no valor cobrado de R$ 15.396,77. Os números de checkout foram conferidos por recálculo independente a partir dos arquivos brutos.
- **Remessa**: R$ 39.543,45 em **uma nota** para a Ponte (232 operações únicas; 4 spreads negativos fora).
- **Divergências de remessa** (valor cheio, a contestar): Mundo Aberto R$ 1.418,88 em 23 operações (P16); spreads negativos R$ 3.565,98 em 4 operações.
- **Atlas retida**: 57 linhas, que o fechamento de outubro precisa puxar.
- **Remessa fecha com o banco**: cada um dos 21 TEDs para a Ponte é a soma de (Valor R$ + IOF) das operações do dia, e o PIX de cada lojista é a soma das suas operações (13 de 14 exatos). A exceção é o PIX de R$ 18.240,00 (R19).
- **Checkout não fecha com o banco**, e o financeiro disse que não é preciso neste fechamento (R24).
- **Estornos de venda de agosto**: 9 linhas, −R$ 941,70 de taxa, abatendo a comissão de setembro.

---

## 5. Decisões de arquitetura

- **Dados como vêm**: nada é corrigido na origem. Limpeza só em colunas derivadas.
- **Regras como dado**: cada decisão do financeiro é uma linha em `config/` com fonte, quem aprovou e quando. O código lê; não tem `if` escondido.
- **Sem banco transacional**: processamento em lote. Atomicidade por publicação em `saida/` só depois das validações.
- **IA só onde há ambiguidade**: classificação de lançamentos sem padrão claro e sugestão de lojista por nome (sempre com confiança baixa e revisão humana). Números vêm sempre do código, com rastro.
- **Versionamento**: um commit por versão, pela skill `commit-versao`.
