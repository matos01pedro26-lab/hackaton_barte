# Hipóteses, regras e perguntas: fechamento Tarvo set/2026

Este arquivo separa o que o financeiro **confirmou**, o que o **time** decidiu (porque a Helena delegou) e o que foi **suposição da IA** e virou pergunta. As regras que se repetiam foram **fundidas em 35 regras consolidadas** (seção 1), cada uma com o motivo. O catálogo item a item, com as 26 regras de classificação dos extratos, está em [REGRAS_NEGOCIO.md](REGRAS_NEGOCIO.md); as perguntas prontas para o canal estão em [PERGUNTAS_FINANCEIRO.md](PERGUNTAS_FINANCEIRO.md).

**Fontes oficiais:** `01_instrucoes_participantes.docx` e as respostas do time financeiro em `duvidas_financeiro.csv` (as respostas aparecem postadas pelo perfil `@manuel.freitas` e assinadas "Helena, financeiro da Tarvo"; tratamos como o mesmo interlocutor). `#n` é a posição da linha nesse CSV. `HIPOTESES.md` e `PLANO.md` são nossos e **não** são regra confirmada.

**Numeração:** os ids antigos `R` e `P` continuam existindo porque o código, os testes e os `config/` os citam (R1, R5, R8, R24, R28, R29…). A seção 5 diz em qual regra consolidada cada um foi absorvido.

**Dados de entrada:** ficam todos em `input/`. Além dos 6 arquivos base, chegou depois o `06_orbe_ajustes_tardios_set2026.csv` (14 lançamentos da Orbe de 30/09). A ingestão lê qualquer arquivo no formato da Orbe do mesmo mês e o grava em `fato_orbe` com o `arquivo_origem` e o `lote` (`BASE` ou `TARDIO`), conferindo que cada ajuste aponta para uma linha existente, de valor oposto, mesma taxa e mesmo EC.

## Legenda: `MTD_INFERENCIA`

| Valor | Significado |
|---|---|
| FINANCEIRO | Dito de forma explícita e direta pela Helena. |
| TIME | A Helena delegou ("o critério é de vocês", "escolham uma e escrevam o motivo") ou é decisão de desenho nossa. Falta o time ratificar. |
| IA | Suposição da IA sem resposta que a sustente. Virou pergunta e **não vale como regra**. |

---

## 0. Resumo (contagem feita sobre as tabelas abaixo)

- **35 regras consolidadas** no lugar de 51 itens R e P: 33 FINANCEIRO, 2 TIME e 0 IA. Das 33 FINANCEIRO, 7 têm uma parte que é escolha do time, e 3 têm uma parte que é critério nosso (RC-07, RC-23 e RC-29).
- **Itens antigos (51)**: 39 FINANCEIRO, 10 TIME, 1 IA e 1 superada.
- **Perguntas abertas: nenhuma.** A rodada 2 (N1 a N10) foi respondida em 17/10 e fechada na seção 3. O que sobra é premissa com dono, e não suposição.
- **Respondidas no T-800:** juros da conta garantida (fora de setembro), IOF de R$ 48,21 (conta nossa), IOF das remessas (do cliente), razão social, CNPJ de 14 dígitos, retenção da Ponte (nenhuma), Fluente a 0,79%, isenção da Casa até 31/12, data da venda, PIX enviado a lojista, rendimento e seguro, contas de bancos, prazo da Ponte (premissa com risco, N1).
---

## 1. Regras de negócio consolidadas (35)

| id | Regra | Motivo | MTD_INFERENCIA | Parte que não é da Helena | Absorve | Fonte | RN |
|---|---|---|---|---|---|---|---|
| **Checkout** | | | | | | | |
| RC-01 | A comissão é **bruto × taxa contratada**: a taxa inteira, sem abater custo da Orbe, e não o `valor_taxa` que a Orbe informou. | A Tarvo fatura o contrato. Se a Orbe cobrou diferente, isso é divergência, não comissão. A Orbe já liquida o líquido, com a taxa descontada na hora, e não há custo a abater neste modelo. | FINANCEIRO |  | R1 | #3, #12, #20 | RN-01, 02 |
| RC-02 | **Estorno** devolve a taxa e abate a comissão **do mês do estorno**, pela taxa da **data da venda original**, mesmo de venda de agosto. A faixa (modalidade e parcelas) vem da linha do estorno. | Agosto já está fechado e não reabre. A taxa que se devolve é a que foi cobrada na venda. A competência do checkout é o mês do movimento. | FINANCEIRO |  | R2, P4 | #1, #12, #14, #28 | RN-03, 04 |
| RC-03 | **Antecipação** entra na mesma nota; a **reversão** só anula a taxa da antecipação que ela reverte. | É o mesmo serviço, do mesmo lojista, no mesmo mês; a reversão desfaz a original. | FINANCEIRO |  | R3 | #3, #12 | RN-05 |
| RC-04 | **Arredondamento** comum, linha por linha e depois soma; meio centavo para cima, também no negativo. Diferença de centavo por truncamento da Orbe **não** é divergência. | A Orbe trunca e a Tarvo não. A Helena não quer alarme de centavo, mas também não quer deixar passar diferença de verdade. | FINANCEIRO |  | R4 (1ª parte) | #7 | RN-07 |
| RC-05 | **Divergência de checkout** = bruto × (taxa aplicada − contratada), **transação por transação**; o estorno de venda com taxa errada entra com valor negativo. | É o valor que o lojista pagou a mais e que se contesta. Listar por transação permite achar a origem de cada centavo. | FINANCEIRO |  | R5 | #7, #28 | RN-08, 09 |
| RC-06 | Quando a contraparte **cobra diferente do contrato**, é divergência: contesta-se a Orbe ou a Ponte e o lojista é ressarcido. Vale para Rota Global (contrato não mudou), Bridge (aditivo de 2,19% desde 15/09), Mundo Aberto (1,20% desde julho) e para a Orbe cobrando **abaixo** do contrato (caso a caso). | O que decide é o contrato, não o aviso. O aviso atrasado é problema de processo nosso, mas não muda quem deve. | FINANCEIRO |  | R9, R29, R35 (e exemplos de R5 e R17) | #5, #14, #27 | RN-10, 26 |
| RC-07 | **Casa do Estudante**: tarifa zerada de setembro a dezembro (MDR e antecipação; remessa normal), com período confirmado pela Helena (01/09 a 31/12/2026). O que a Orbe cobrou é **devolução nossa**, separada das divergências e fora da cobrança da Orbe, no valor descontado de fato (R$ 15.396,77). A isenção da antecipação vale pela **data da antecipação**. | É concessão do comercial, fora do contrato. A Orbe cobrou certo pelo que sabia, então quem abriu mão da receita arca com a devolução. | FINANCEIRO | IA: o que acontece depois de dezembro, volta à planilha em 2027 (N3). | R8, R28, R45, P2, P14 | #5, #14, #21, #27, #30, #33, #35 | RN-11 a 15 |
| RC-08 | **Atlas** (sem contrato): não fatura, vira pendência e fica **fora** de `comissoes_por_lojista`; o repasse segue normal. Quando o comercial confirmar, a taxa vale desde 10/09 e outubro puxa as linhas de setembro. O CNPJ da aba de 2025 só identifica. | O dinheiro é do lojista. O que fica suspenso é só o faturamento da nossa taxa, até haver taxa. | FINANCEIRO | TIME: ficar fora do arquivo em vez de zerada, e o PIX em `2.1.01.001` como repasse normal (P17, P12). | R7, R31, P12, P17 (parte) | #2, #16, #24, #28, #29 | RN-17 a 20 |
| RC-09 | **Mapeamento de ECs**: 1043300981 é a Novo Horizonte Intercâmbio; 1043396662, a Horizonte Viagens e Turismo (empresa diferente); 1038867654, a Kiwi Experience. | O EC estava em branco na planilha de taxas; CNPJ e taxas estão nas linhas delas. | FINANCEIRO |  | R6 | #2 | RN-21 |
| RC-10 | Venda **acima de 12 parcelas** não existe; se aparecer, é pendência. | A Tarvo não vende acima de 12x. | FINANCEIRO |  | R33 | #23 | RN-22 |
| RC-11 | Estorno com **bandeira diferente** da venda segue o vínculo pela referência, sem contestar nem abrir pendência. | A bandeira não muda a taxa, e a Orbe às vezes troca a bandeira no estorno. | FINANCEIRO |  | R34 | #37 | RN-23 |
| RC-12 | **Ajustes tardios da Orbe** entram no mês do movimento se chegarem antes de a Helena aprovar o fechamento; depois disso, no mês seguinte. | Depois da aprovação o mês está fechado. | FINANCEIRO | TIME: ajuste com o **mesmo id** de uma linha do relatório nunca aconteceu; o critério é nosso, com pendência para a Helena (R47, ainda não escrito). | P13, R46, R47 | #36 | RN-27, 28 |
| RC-13 | O **alerta de antecipação** acima do vendido é critério do time; vai para a Helena e o comercial e **não muda nenhum número**. | Não há trava de antecipação, e a agenda inclui vendas de meses anteriores que o relatório não traz. A preocupação dela é lojista novo antecipando alto (Atlas). | TIME |  | R32 | #14, #27, #30, #32 | RN-25 |
| RC-14 | Comissão **zero ou negativa** (Casa, −R$ 5,50): **não emite nota** e vira pendência para a Helena; o negativo não passa para o mês seguinte automaticamente. | A Helena trata o saldo negativo diretamente com o lojista. | FINANCEIRO | TIME: a linha negativa fica em `comissoes_por_lojista` com o valor real (P17). | R10 (parte), R27 (parte), P17 (parte) | #3, #26, #28 | RN-29, 51 |
| **Notas** | | | | | | | |
| RC-15 | **Checkout**: uma nota por lojista por mês, no valor da comissão do mês pela taxa contratada, com texto simples (serviço e competência). A nota só documenta a taxa que a Orbe já descontou e não gera cobrança nova. | O lojista já recebeu o líquido; a nota é documento, não cobrança. Por isso, se a Orbe cobra a mais, a Helena precisa devolver. | FINANCEIRO |  | R10, R40 | #3, #20 | RN-50, 53, 54 |
| RC-16 | **Remessa**: uma nota só, com a **Ponte Câmbio** como tomadora, pelo total da participação do mês. Não há nota por lojista. | Quem paga a Tarvo na remessa é a Ponte. | FINANCEIRO |  | R11 | #3 | RN-52 |
| **Remessa** | | | | | | | |
| RC-17 | A comissão é **50% do Spread R$ realizado**, arredondada **por operação** (R$ 131,005 vira R$ 131,01). Spread em branco ou "padrão" = **1,5% sobre a PTAX**. | É como a Ponte divide o spread com a Tarvo, e o padrão é o do contrato. | FINANCEIRO |  | R12, R13, R4 (2ª parte) | #4, #7 | RN-30, 31, 32 |
| RC-18 | **Spread negativo**: fora da comissão e da nota; é pendência de contestação, **não** divergência, com os dois valores rotulados (o do relatório e a diferença até o spread do contrato). | A trava vale 2 horas pelo contrato e essas passaram do prazo. O lojista não pagou a mais; o prejuízo é da Tarvo com a Ponte, e o que se pede à Ponte é a trava honrada. | FINANCEIRO | TIME: listar também em divergências é opcional, se for rotulado como outra natureza. | R14, R30, R36 | #4, #13, #27 | RN-33 a 35 |
| RC-19 | **Operação repetida**: o número da operação é único; conta uma vez e entra na lista de correção da Ponte. | A Ponte soma as duas linhas e repassaria a mais. "Conta uma vez" é leitura nossa da frase dela. | FINANCEIRO |  | R15 | #4, #10 | RN-36 |
| RC-20 | "Aprovado c/ ressalva" **não muda nada**. Vale a **data de contratação**, não a de liquidação. | Compliance não afeta a comissão; a competência é a contratação. | FINANCEIRO |  | R16 | #4 | RN-37, 38 |
| RC-21 | **Divergência de remessa**: o lojista pagou spread diferente do contratado (Mundo Aberto, 1,20%). O valor é o **cheio**, não os 50%. | O total é o que se contesta com a Ponte; a nossa metade é só a divisão do spread. | FINANCEIRO | TIME: a fórmula usa o Spread R$ realizado (R$ 1.418,88 contra R$ 1.418,85 pelo `spread_pct`) e a tolerância é de 0,005 p.p. (P16, P1). | R17 (1ª parte), P1, P16 | #4, #6, #14, #23 | RN-39 a 41 |
| RC-22 | A **nota da Ponte sai pelo realizado**, inclusive o excesso contestado. O **ajuste da Ponte** (linha nova "AJUSTE REF PC-…", Spread R$ negativo) entra no mês em que aparece e abate a participação dentro da nota única, sem nota complementar. | É o que a Ponte repassa agora. A contestação é processo à parte e o mês fechado não reabre. | FINANCEIRO |  | R17 (2ª parte), R18 (2ª parte), R27, P9 | #9, #26, #28 | RN-42, 43 |
| RC-23 | **Contestação à Ponte**: uma pendência por contraparte e por lojista, com o detalhe das transações; um rascunho de e-mail por contraparte, que a Helena revisa e envia. Não contar com desconto no repasse; conferir o TED quando cair. | É o formato que a Helena usa para contestar. A contestação nem foi aberta. | FINANCEIRO | IA: que ainda esteja no prazo (N1). Aviso: as pendências de spread negativo estão por operação, não por lojista. | R18 (1ª parte), R37, R39, R42 | #10, #18, #23 | RN-44, 47, 48, 60 |
| RC-24 | Operação da Ponte de **CNPJ fora da planilha**: calcular a nossa metade mesmo assim e abrir pendência de cadastro para o comercial. | A Ponte paga e a nota precisa bater com o repasse. Não ocorreu em setembro. | TIME |  | R38 | #15 | RN-45 |
| **Bancos** | | | | | | | |
| RC-25 | `conta_codigo` é a **contrapartida** do movimento no banco: se o valor já estava registrado, o pagamento ou recebimento **baixa a conta onde estava** e não vira receita ou despesa de novo. | Evita contar duas vezes o que já foi apropriado. | FINANCEIRO |  | R20 | #8 | RN-63 |
| RC-26 | **Já provisionados**: folha, ISS, INSS, FGTS e DARFs de agosto (todo mês a folha e os impostos do mês ficam provisionados) e o repasse de comissão da Ponte de 04/09 (spread de agosto, já comissão a receber). **Todo o resto** (tarifas, aluguel, cloud, assinaturas, serviços) vai direto para a despesa do mês. A provisão de setembro é da contabilidade. | O pagamento do mês seguinte baixa a provisão. Quando o extrato não deixa claro, declara-se a premissa e segue. | FINANCEIRO |  | R21, R44 | #5, #8, #17, #30 | RN-64 a 68 |
| RC-27 | **Fluxo da Orbe**: deposita tudo no Aurora (débito e Pix no dia seguinte; crédito e parcelado ao longo dos meses). O saldo negativo do Aurora é a **conta garantida**. O repasse é feito perto dos dias 10 e 24, do que a Orbe já liquidou, e pode ser antecipado pela conta garantida, sem limite escrito. **Não** se concilia parcela a parcela. | O que entra no banco em setembro não bate com o líquido do relatório do mês. Conciliar a Orbe contra o banco não é o que a Helena precisa neste fechamento. | FINANCEIRO |  | R24, R25 | #11, #20, #22 | RN-69 a 71 |
| RC-28 | **Lançamentos sem origem**: o PIX de R$ 7.350 sem identificação **não é receita**; a devolução de R$ 12.400 é um PIX de repasse que voltou; os R$ 300.000 estão em trânsito (saem do Aurora em 30/09 e caem no Meridiano em 01/10); o PIX de R$ 18.240 da Ponte Aérea é remessa de outubro. | Cada um depende de um fato que a Helena deu, e o tratamento é decisão do time, com o motivo escrito. | FINANCEIRO | TIME: as contas (`1.1.09.002`, `2.1.01.001` ou `2.1.01.002`, `1.1.09.001`, `2.1.02.001`) e a escolha de uma só para a devolução (R23, P5, P6, P8). | R19, R22, R23, P5, P6, P7, P8 | #5, #14, #15, #17, #34 | RN-46, 72 a 74 |
| RC-29 | **Classificação dos extratos por regra** (26 regras em `src/classificacao.py`): 8 contas decorrem da resposta da Helena (folha, INSS, FGTS, ISS, três DARFs e a comissão da Ponte); A03, M06 e M08 foram confirmadas no T-800 (itens 9 e 10); 16 são escolha do time; 2 (M02, TED à Ponte, e M05, CDB) seguem como suposição nossa (N9). | A Helena não valida conta por conta (#23, #24); validou o critério. O detalhe regra a regra está em `REGRAS_NEGOCIO.md`. | FINANCEIRO | TIME: 16 contas. critério nosso em `M02_TED_PONTE` e `M05_CDB` (N9). | P7 e P12 (contas), P10 (parte) | #8, #23, #24 | seção 4 de REGRAS_NEGOCIO |
| **Governança** | | | | | | | |
| RC-30 | **Quem aprova**: taxa, condição comercial e cadastro ou contrato, o comercial (a Helena registra); a regra de como fechar, a Helena. Registrar quem aprovou e quando. | A Bia mantém a planilha, mas não decide taxa. Nas férias da Helena, hoje ninguém fecha. | FINANCEIRO |  | R26, R41 | #19, #23 | RN-58, 59 |
| RC-31 | Quando falta fonte ou informação, **fecha-se o que não depende dela**, marca-se o provisório e o bloqueado, e a Helena libera. Se o layout de um arquivo mudar, a solução avisa em vez de quebrar calada. | A Helena não segura o mês inteiro; já houve arquivo atrasado e parceiro mudando layout sem avisar. | FINANCEIRO |  | R43 | #31 | RN-61, 62 |
| **Suposições da IA** | | | | | | | |
| RC-32 | **Fluente**: o Pix a 0,79% é condição negociada com a Fluente (resposta ao T-800, item 7). Fica como está na planilha, sem pendência. A pendência de R$ 9,16 era só a diferença para 0,89% e foi retirada. | A nota da Fluente (R$ 7.316,07) já usava 0,79%. | FINANCEIRO |  | P15 | resposta ao T-800 (7) | RN-24 |
| RC-33 | A taxa de uma **venda** vale pela data da venda (ex.: aditivo da Bridge "a partir de 15/09"). | Confirmado pela Helena (resposta ao T-800, item 9). O estorno olha a data da venda original; para a venda, vale a data da venda. | FINANCEIRO |  | P3 | resposta ao T-800 (9) | RN-16 |
| RC-34 | Na nota, **razão social** pelo nome da planilha com o CNPJ; a Bia confere na emissão, e a razão social do contrato de adesão não está no pacote. CNPJ sempre com 14 dígitos (Fluente e Campus Global com o zero restaurado). | Respostas 4 e 5 do T-800. | FINANCEIRO |  | P11 | resposta ao T-800 (4, 5) | RN-55, 56 |
| RC-35 | O **IOF** das remessas é do cliente: a Tarvo só repassa à Ponte. O IOF s/ crédito de R$ 48,21 é de operação do Meridiano e vai para `4.3.01` (a conta é decisão nossa). **Sem retenção** de ISS ou IRRF pela Ponte; o ISS da nota vai no DAMSP do mês seguinte, fora deste fechamento. | Respostas 2, 3 e 6 do T-800. | FINANCEIRO |  | P10 | resposta ao T-800 (2, 3, 6) | RN-57 |

---

## 2. Decisões do time, com o motivo e o risco (`MTD_INFERENCIA = TIME`)

A Helena não valida essas escolhas; pediu que fossem escritas, com o motivo. **O time ainda precisa ratificar cada uma.**

### 2.1 Delegadas pela Helena

| # | Decisão | Fonte | Por quê | Se estiver errada |
|---|---|---|---|---|
| R23 | Devolução de PIX em `2.1.01.001` ou `2.1.01.002`: "as duas fazem sentido; escolham uma, mantenham o mesmo critério e escrevam o motivo". | #5, #17 | A Helena aceita as duas contas. | Reclassificar entre `2.1.01.001` e `2.1.01.002`. |
| R32 | **Alerta de antecipação**: o critério é da equipe, porque a agenda inclui vendas de meses anteriores que o relatório não traz. Não há limite definido pelo financeiro. | #14, #27, #30, #32 | A agenda de antecipação inclui vendas de meses anteriores que o relatório não traz. O alerta não muda nenhum número. | Alarme falso para a Helena ou alerta perdido. |
| P1 | **Tolerância de 0,005 p.p.** entre o spread aplicado e o contratado (em `config/parametros.csv`, fonte única da ingestão e do módulo de remessa). | #6, #7 | O ruído do spread da Ponte fica em ±0,0016 p.p., sem viés por lojista; a única divergência real de setembro (Mundo Aberto) está em +0,30 p.p. 0,005 p.p. é 3 vezes o ruído e 60 vezes menor que a divergência real. Em reais não separa bem (o ruído chega a R$ 0,70 e cresce com a operação). Estudo: `notebooks/remessa_tolerancia.ipynb`. | Abaixo disso viraria alarme de centavo; acima, perderíamos diferença real. Um mês só: rever com outubro. |
| P5 | **Devolução de PIX (R$ 12.400,00)** em `2.1.01.001` (Repasses a lojistas a pagar). | #5, #17 | A Helena descreveu como "um PIX de repasse que voltou": o repasse volta a ser devido. | Se for devolução ao lojista, seria `2.1.01.002`. |
| P6 | **PIX de R$ 7.350,00** em `1.1.09.002` (Créditos não identificados). | #5 | "Não é receita até alguém identificar." | Se identificarem, reclassifica. |
| P8 | **Transferência de R$ 300.000,00** de 30/09 em `1.1.09.001` (Transferências entre contas próprias). Entrada no Meridiano só em 01/10. | #5 | R22. | Sem contrapartida no mês até a entrada. |
| P16 | O **valor da divergência de remessa** é `Spread R$` realizado − spread contratado × Valor ME × PTAX (valor cheio), em `Decimal`, arredondado ao centavo por operação. | #23 | Usa o valor que a Ponte pagou, sem passar pelo `spread_pct` do relatório, que vem arredondado. | Pelo `spread_pct` a Mundo Aberto daria R$ 1.418,85 em vez de R$ 1.418,88 (3 centavos). |
| P17 | **Comissão de checkout zero ou negativa fica em `comissoes_por_lojista` com o valor real** e vira pendência `COMISSAO_NAO_POSITIVA` (não emite nota, R10). Em setembro, só a Casa do Estudante (−R$ 5,50). A Atlas fica fora do arquivo (R31, escolha nossa). | #28, #29 | O número precisa fechar com o rastro; a regra de não emitir é da nota, não da comissão. | Se o gabarito tirar a linha, o total de checkout sobe R$ 5,50 e a Casa sai do arquivo. |

### 2.2 Decisões de desenho (não são regra de negócio)

| # | Decisão | Por quê | Se estiver errada |
|---|---|---|---|
| P18 | **Ids do checkout**, no mesmo padrão da remessa: `CHK-AAAA-MM-<cnpj>` (comissão), `DIV-CHK-AAAA-MM-<id_transacao>` (divergência) e `PEN-CHK-AAAA-MM-<tipo>-<chave>` (pendência). Nas pendências, `ref_origem` lista as transações da Orbe separadas por `|`, como a `CONTESTACAO_PONTE`. | Chaves naturais, estáveis entre meses; o rastro leva cada número às linhas de origem. | Só muda o identificador, não os valores. |
| P19 | **Valor de cada pendência do checkout = o que está em jogo**: EC retido = soma do bruto (não há taxa contratada); `CONTESTACAO_ORBE` = soma das divergências do lojista (R29); `DEVOLUCAO_CONDICAO` = o que a Orbe cobrou, `valor_taxa` (R28); `CADASTRO_EC` = comissão que depende do mapeamento em `config/`; `CADASTRO_CONDICAO` = comissão que a planilha cobraria; `TAXA_A_CONFIRMAR` = quanto a comissão mudaria (P15); sem taxa = bruto. | Dá ao financeiro o tamanho de cada decisão, sempre com rastro até as transações. | Só muda a coluna `valor_brl` de `pendencias.csv`. |
| P20 | **Mês fechado não reabre.** Quando o validador passa, `src.fechar` arquiva o mês em `fechamentos/AAAA-MM/` (saída, tabelas, manifesto com o sha256 de cada arquivo de entrada e pendências abertas), e rodar o mesmo mês de novo para com aviso. O que chegar depois de um mês fechado entra no mês aberto, como o estorno de agosto (RC-02), o ajuste da Ponte (RC-22) e os ajustes tardios da Orbe depois da aprovação (RC-12). Pela RC-12 o mês fecha quando a Helena aprova: até lá, rode com `--sem-arquivar`; arquivar é registrar a aprovação. `--refazer` existe só para corrigir um fechamento errado e guarda o anterior em `anterior_<hora>/`. | Agosto já fechado não reabre (R2); a Ponte registra o ajuste no mês em que aparece (R27). Decisão do grupo em 17/10. | Se a Helena preferir reabrir, o fechamento refeito vira versão nova e a diferença precisa de nota complementar. |
| P21 | **O histórico é a prova do que já foi faturado.** O `rastro.csv` arquivado diz quais transações da Orbe (`CHK-…`) e operações da Ponte (`REM-…`) entraram em comissão. Transação da Orbe já faturada que reaparece num mês seguinte **para o fechamento** (cobrança em dobro). Operação da Ponte já faturada que reaparece (contratada num mês e liquidada no seguinte, P4) vira `JA_FATURADA`: conta uma vez e não gera pendência. As pendências abertas passam para o mês seguinte até alguém registrar a decisão em `config/pendencias_resolvidas.csv`. | Sem histórico, outubro não sabe o que setembro faturou. | Se a Ponte renumerar operações entre meses, a checagem por Nº de operação não pega a repetição. |

### 2.3 Delegadas pela Helena e ainda não escritas neste arquivo

| # | Decisão | Fonte | O que falta |
|---|---|---|---|
| R38 | Operação da Ponte de **CNPJ fora da planilha**: calcular a nossa metade mesmo assim e abrir pendência de cadastro para o comercial. Registrar como premissa. Não ocorreu em setembro. | #15 | Conferir se `flag_cnpj_fora_da_tabela` gera a pendência. |
| R47 | Ajuste tardio da Orbe com o **mesmo id** de uma linha do relatório: nunca aconteceu. O critério é do time, com pendência para a Helena. | #36 | Escrever o critério. |

---

## 3. Premissas fechadas na rodada 2 (T-800, 17/10)

Nenhuma suposição da IA segue aberta. Cada item abaixo tem a decisão, quem decide e o que muda se estiver errado. Esses ficam também como `pendencias.csv` quando dependem de alguém.

| # | Item | Resposta / decisão | Quem decide | Se estiver errada |
|---|---|---|---|---|
| N1 | Prazo da contestação à Ponte | A Helena disse que ainda estamos no prazo, porque o fechamento é esta semana. Essa é a premissa da Helena, **não** confirmada pela Ponte: o e-mail de 02/10 (5 dias úteis) venceu em 09/10. **Decisão nossa:** a contestação só é enviada com a data confirmada por escrito pela Ponte. | Helena (financeiro) | A Ponte pode recusar a contestação (Mundo Aberto, spreads negativos, duplicata). |
| N2 | Valor pedido à Ponte na Mundo Aberto | Decisão nossa: **R$ 1.418,88** (Spread R$ realizado, o que a Ponte paga). A diferença é de centavos, e a Helena pediu para registrarmos o critério (RN-40). | Equipe | Três centavos. |
| N3 | Casa do Estudante em 2027 | Renovar ou não é decisão do comercial, sem previsão. A Casa segue sem condição depois de 31/12/2026, e a pendência está com o comercial. | Comercial | Se a isenção continuar, a tabela precisa de nova condição em `config/condicoes_comerciais.csv`. |
| N4 | PIX de R$ 7.350 sem identificação | A conta 1.1.09.002 segue como critério nosso. O Caio vai atrás do pagador com o banco até o fechamento de outubro. | Caio (bancos) | Reclassifica quando identificado. |
| N5 | Devolução de R$ 12.400 | Decisão nossa: **2.1.01.001** (a Helena disse que as duas contas servem). | Equipe | Reclassificar entre 2.1.01.001 e 2.1.01.002. |
| N6 | Transferência de R$ 300.000 | A conta 1.1.09.001 segue como critério nosso. Se a entrada no Meridiano não aparecer em outubro, a pendência vai para a tesouraria, que é a Helena. | Helena (tesouraria) | Sem contrapartida no mês até a entrada. |
| N7 | PIX de R$ 18.240 da Ponte Aérea | Confirmado: é remessa de outubro. A baixa sai quando a remessa liquidar, pelo relatório de outubro da Ponte. | Helena (financeiro) | — |
| N8 | Contas de despesa (A02, A12, A13, A14, A15, M07, M08) | A regra geral é confirmada (despesa do mês vai direto na despesa). As contas específicas são critério nosso, registradas aqui. | Equipe | Reclassificar a conta, sem efeito no total. |
| N9 | TED à Ponte (M02) e CDB (M05) | Confirmado no princípio: o TED da Ponte baixa recurso de lojista (passivo, 2.1.02.001) e o CDB não tem efeito no resultado (1.1.02.001). A conta segue como critério nosso. | Equipe | Reclassificar a conta. |
| N10 | Atlas (EC 1076801732) | Quem decide a taxa é o Diego, do comercial, sem previsão. A Atlas segue retida. | Comercial (Diego) | Sem taxa, a Atlas fica fora do faturamento. |

---

## 4. Superadas ou resolvidas

| Item | Resultado |
|---|---|
| P9 | Superada pela R27: a Helena respondeu como o ajuste da Ponte aparece. Mantida abaixo como histórico. |
| P13 | Confirmada pela #36 (absorvida na RC-12). |
| "Em aberto" 1: regra do repasse | Respondida na #22: pela regra é o que a Orbe já liquidou, e na prática a Bia às vezes paga antes pela conta garantida, sem limite escrito. |
| "Em aberto" 7: ajustes tardios da Orbe | Respondida na #36 (RC-12). |
| "Em aberto" 8: reversões tardias de antecipação | Descartada: a #11 diz que não é preciso conciliar a Orbe contra o banco neste fechamento. |
| As oito premissas antigas | Confirmadas pelo financeiro (R1 a R5, R6/R7, R12, R13, R15, R16). |
| Juros da conta garantida (T-800, item 1) | Vêm no extrato do mês seguinte. A pendência `CONTA_GARANTIDA_SEM_ENCARGOS` foi removida: o −R$ 2.289.532,94 era saldo, não valor a lançar. |
| Fluente, Pix a 0,79% (T-800, item 7) | Condição negociada. A pendência `TAXA_A_CONFIRMAR` (R$ 9,16) foi removida, e `config/taxas_a_confirmar.csv` ficou só com o cabeçalho. A nota já usava 0,79%, então nenhum valor mudou. |
| DARF sem competência (#5, #17) | A Helena disse que são de agosto e já estavam provisionados. As 3 pendências `DARF_SEM_COMPETENCIA` ainda estão no arquivo e precisam ser fechadas; ver nota ao final. |

### Detalhe da P9 (contribuição do Gabriel, commit `90d0d6b`; superada pela R27, mantida como histórico)

- **Status:** superada pela R27 (resposta da Helena às 11h33 de 17/10).
- **Contexto:** a Helena disse que a Ponte comunica o resultado de uma contestação por e-mail e envia o ajuste no relatório do mês seguinte, como crédito ou débito, e que ela registra o ajuste no fechamento do mês em que ele aparece. O relatório de setembro não tem nenhuma linha assim, então o formato dessas linhas é desconhecido.
- **Decisão:** no fechamento de outubro, qualquer linha do relatório da Ponte que não seja uma operação de câmbio normal (por exemplo, crédito ou débito de ajuste) não entra na comissão nem na nota. Ela vira pendência em `pendencias.csv`, com valor e motivo, para a Helena decidir.
- **Por quê:** o formato do ajuste não está nos dados. Tratar uma linha desconhecida como operação normal poderia faturar um valor errado. Parar e pedir decisão é a opção mais segura, e a Helena já pediu pendência para o que foge da regra.
- **Origem:** resposta 6 à pergunta da Turma do Barulho (canal #tarvo-financeiro, 17/10).

---

## 5. Mapa: onde cada id antigo foi parar

Itens R33 a R47 são respostas da Helena que o arquivo antigo não tinha (R38 e R47 são do time).

| id antigo | MTD_INFERENCIA | Regra consolidada |
|---|---|---|
| P1 | TIME | RC-21 |
| P2 | FINANCEIRO | RC-07 |
| P3 | FINANCEIRO | RC-33 |
| P4 | FINANCEIRO | RC-02 |
| P5 | TIME | RC-28 |
| P6 | TIME | RC-28 |
| P7 | FINANCEIRO | RC-28, RC-29 |
| P8 | TIME | RC-28 |
| P9 | SUPERADA | RC-22 |
| P10 | FINANCEIRO | RC-29, RC-35 |
| P11 | FINANCEIRO | RC-34 |
| P12 | FINANCEIRO | RC-08, RC-29 |
| P13 | FINANCEIRO | RC-12 |
| P14 | IA | RC-07 |
| P15 | FINANCEIRO | RC-32 |
| P16 | TIME | RC-21 |
| P17 | TIME | RC-08, RC-14 |
| P18 | TIME | sem regra de negócio (desenho) |
| P19 | TIME | sem regra de negócio (desenho) |
| P20 | FINANCEIRO | RC-02, RC-12, RC-22 |
| P21 | TIME | sem regra de negócio (desenho) |
| R1 | FINANCEIRO | RC-01 |
| R2 | FINANCEIRO | RC-02 |
| R3 | FINANCEIRO | RC-03 |
| R4 | FINANCEIRO | RC-04, RC-17 |
| R5 | FINANCEIRO | RC-05, RC-06 |
| R6 | FINANCEIRO | RC-09 |
| R7 | FINANCEIRO | RC-08 |
| R8 | FINANCEIRO | RC-07 |
| R9 | FINANCEIRO | RC-06 |
| R10 | FINANCEIRO | RC-14, RC-15 |
| R11 | FINANCEIRO | RC-16 |
| R12 | FINANCEIRO | RC-17 |
| R13 | FINANCEIRO | RC-17 |
| R14 | FINANCEIRO | RC-18 |
| R15 | FINANCEIRO | RC-19 |
| R16 | FINANCEIRO | RC-20 |
| R17 | FINANCEIRO | RC-06, RC-21, RC-22 |
| R18 | FINANCEIRO | RC-22, RC-23 |
| R19 | FINANCEIRO | RC-28 |
| R20 | FINANCEIRO | RC-25 |
| R21 | FINANCEIRO | RC-26 |
| R22 | FINANCEIRO | RC-28 |
| R23 | TIME | RC-28 |
| R24 | FINANCEIRO | RC-27 |
| R25 | FINANCEIRO | RC-27 |
| R26 | FINANCEIRO | RC-30 |
| R27 | FINANCEIRO | RC-14, RC-22 |
| R28 | FINANCEIRO | RC-07 |
| R29 | FINANCEIRO | RC-06 |
| R30 | FINANCEIRO | RC-18 |
| R31 | FINANCEIRO | RC-08 |
| R32 | TIME | RC-13 |
| R33 | FINANCEIRO | RC-10 |
| R34 | FINANCEIRO | RC-11 |
| R35 | FINANCEIRO | RC-06 |
| R36 | FINANCEIRO | RC-18 |
| R37 | FINANCEIRO | RC-23 |
| R38 | TIME | RC-24 |
| R39 | FINANCEIRO | RC-23 |
| R40 | FINANCEIRO | RC-15 |
| R41 | FINANCEIRO | RC-30 |
| R42 | FINANCEIRO | RC-23 |
| R43 | FINANCEIRO | RC-31 |
| R44 | FINANCEIRO | RC-26 |
| R45 | FINANCEIRO | RC-07 |
| R46 | FINANCEIRO | RC-12 |
| R47 | TIME | RC-12 |

---

## 6. Fusões aplicadas

| Situação que se repetia | Itens | Regra consolidada |
|---|---|---|
| Competência: mês do movimento (checkout) e da contratação (remessa) | R2, R16, P4 | RC-02 e RC-20 |
| Arredondamento da remessa por operação | R4, P16 | RC-04, RC-17 e RC-21 |
| Atlas: não fatura, vira pendência, repasse segue normal | R7, R31, P12, P17 | RC-08 |
| Casa do Estudante: isenção e devolução | R8, R28, R45, P2, P14 | RC-07 |
| Zero ou negativo não emite nota | R10, R27, P17 | RC-14 |
| Contraparte cobrou diferente do contrato | R5, R9, R17, R29, R35 | RC-06 |
| Ajuste da Ponte no mês seguinte | R18, R27, P9 | RC-22 |
| Tolerância do spread | R17, P1 | RC-21 |
| Três lançamentos sem origem | R22, R23, P5, P6, P8 | RC-28 |
| PIX de R$ 18.240,00 | R19, P7 | RC-28 |
| Provisionados | R20, R21, R44 | RC-25 e RC-26 |

11 situações fundidas. **Continuam duplicadas, e não são só de texto:** a condição da Casa vive em dois arquivos de `config/` (`condicoes_comerciais.csv`, lido pela ingestão, e `condicoes_especiais.csv`, lido pelo checkout), a unificar antes de outubro (seção 9); e este arquivo e o `REGRAS_NEGOCIO.md` descrevem as mesmas regras com numerações diferentes (aqui estão os motivos e as premissas, que o edital exige; lá está o catálogo item a item).

---

## 7. Perguntas ao financeiro

As 10 perguntas da rodada 2, redigidas com exemplo, estão em [PERGUNTAS_FINANCEIRO.md](PERGUNTAS_FINANCEIRO.md). As respostas já recebidas estão em `duvidas_financeiro.csv` e foram incorporadas na seção 1.

### 7.1 Pendências de cadastro com o financeiro

São dados que pertencem à planilha de taxas, mantida pelo financeiro, e que só conseguimos perguntando. A solução aplica a resposta por `config/`, mas a planilha continua incompleta. Por isso cada item fica **pendente para o financeiro** até a planilha ser corrigida. A coluna `pendencia_financeiro` dos arquivos de `config/` diz o que corrigir e alimenta o `pendencias.csv` do checkout (`CADASTRO_EC` e `CADASTRO_CONDICAO`). Depois da correção na planilha, a linha correspondente em `config/` pode sair.

| Item | O que falta na planilha | Configuração usada hoje | Base |
|---|---|---|---|
| Kiwi Experience | EC Orbe `1038867654` na linha 9 (obs "EC pendente") | `config/mapeamento_ec.csv` | R6 |
| Horizonte Viagens | EC Orbe `1043396662` na linha 8 | `config/mapeamento_ec.csv` | R6 |
| Novo Horizonte Intercambio | EC Orbe `1043300981` na linha 28 | `config/mapeamento_ec.csv` | R6 |
| Casa do Estudante | Taxa zerada de 01/09 a 31/12/2026; a linha 13 só tem o comentário "conversar com Diego (comercial) sobre condição especial" | `config/condicoes_comerciais.csv` (ingestão) e `config/condicoes_especiais.csv` (checkout) | R8 |

---

## 8. Achados que mudam número

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
- **Checkout calculado por `src/checkouts`** (com os ajustes tardios): **R$ 203.735,34 em 21 lojistas** (os R$ 203.740,84 dos 20 com nota menos os −R$ 5,50 da Casa, P17), 1.900 linhas no rastro e 57 da Atlas retidas. **Divergências: 92 linhas, R$ 1.576,23** (Rota Global R$ 1.546,28; Bridge R$ 29,95). São 9 pendências: Atlas (comercial), Casa negativa, devolução da Casa (R$ 15.396,77, R28), 2 contestações com a Orbe (R29) e 4 de cadastro (seção 7.1). Batem com a prévia independente e com o notebook.

---

## 9. Decisões de arquitetura

- **Dados como vêm**: nada é corrigido na origem. Limpeza só em colunas derivadas.
- **Regras como dado**: cada decisão do financeiro é uma linha em `config/` com fonte, quem aprovou e quando. O código lê; não tem `if` escondido.
- **Sem banco transacional**: processamento em lote. Atomicidade por publicação em `saida/` só depois das validações.
- **IA só onde há ambiguidade**: classificação de lançamentos sem padrão claro e sugestão de lojista por nome (sempre com confiança baixa e revisão humana). Números vêm sempre do código, com rastro.
- **Versionamento**: um commit por versão, pela skill `commit-versao`.
- **Código particionado por domínio**: `src/<dominio>/`, com camadas leves dentro de cada um. O checkout está em `src/checkouts/` (leitura → regras → comissão e divergência → saída) e lê só `data/` e `config/`. Os CSVs saem com exatamente as colunas do edital.
- **Testes**: `python -m unittest discover -s tests -t .` (só biblioteca padrão). Os testes do checkout cobrem as regras pela interface pública e garantem determinismo: a mesma entrada em qualquer ordem dá o mesmo resultado, e duas execuções geram os mesmos bytes.
- **Em aberto: condição da Casa em dois arquivos.** A ingestão aplica `config/condicoes_comerciais.csv` em `dim_contrato_taxa` (linha `CONFIG`), e o checkout lê `config/condicoes_especiais.csv` para a taxa, a devolução e a pendência de cadastro. Os dois dizem 0% de 01/09 a 31/12; unificar em um só antes de outubro.
