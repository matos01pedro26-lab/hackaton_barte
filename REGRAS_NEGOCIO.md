# Regras de negócio: o que é do financeiro, do time e da IA

Base: `01_instrucoes_participantes.docx` e as 38 respostas de `duvidas_financeiro.csv`. **#n** é a posição da linha no CSV (a primeira dúvida é #1).

## Como ler `MTD_INFERENCIA`

| Valor | Significado | Gera pergunta? |
|---|---|---|
| **FINANCEIRO** | Dito de forma explícita e direta pela Helena (ou pela organização, quando for o caso). Cito o #n. | Não |
| **TIME** | A Helena **delegou** ("o critério é de vocês", "escolham uma e escrevam o motivo") ou o time definiu no brief (mapeamento de referência de 24 linhas dos extratos). Falta o time ratificar e escrever o motivo no `HIPOTESES.md`. | Não |
| **IA** | Suposição minha, sem resposta que a sustente. Não vale como regra confirmada. | **Sim**: ver `PERGUNTAS_FINANCEIRO.md` (N1 a N10, rodada 2) |

Regras do edital e da organização ficam em seção própria, sem `MTD_INFERENCIA`, porque não são inferência de ninguém.

---

## 1. Checkout

| id | Regra | MTD_INFERENCIA | Base | Observação |
|---|---|---|---|---|
| RN-01 | A comissão é a taxa inteira, **sem abater custo da Orbe**. | FINANCEIRO | #12 | |
| RN-02 | A comissão é calculada pela **taxa contratada** (bruto × taxa da planilha), não pelo `valor_taxa` da Orbe. | FINANCEIRO | #3, #12 | |
| RN-03 | **Estorno** devolve a taxa ao lojista e abate a comissão **do mês do estorno**, inclusive de venda de agosto (agosto já está fechado e não reabre). | FINANCEIRO | #1, #12 | |
| RN-04 | A taxa do estorno é a da **data da venda original**; a faixa (modalidade e parcelas) vem da linha do estorno. | FINANCEIRO | #1, #14, #28 | |
| RN-05 | **Antecipação** entra na mesma nota. A **reversão** só anula a taxa da antecipação que ela reverte. | FINANCEIRO | #3, #12 | |
| RN-06 | Venda cobrada acima do contrato e depois estornada: venda e estorno se anulam; cobra-se da Orbe só a diferença líquida. | FINANCEIRO | #14 | |
| RN-07 | Arredondamento comum para o centavo, meio centavo para cima (no negativo, com o sinal), **linha por linha e depois soma**. A Orbe trunca; a Tarvo não. | FINANCEIRO | #7 | |
| RN-08 | Divergência de checkout = **bruto × (taxa aplicada − contratada)**. Diferença de centavo por truncamento da Orbe não é divergência. | FINANCEIRO | #7 | |
| RN-09 | A lista de divergências é **transação por transação**; o estorno de venda com taxa errada entra com valor negativo. | FINANCEIRO | #28 | |
| RN-10 | **O contrato decide, não o aviso.** Bridge (aditivo de 2,19% desde 15/09) e Rota Global são divergência: contesta-se a Orbe e o lojista é ressarcido. | FINANCEIRO | #5, #27 | |
| RN-11 | **Casa do Estudante**: tarifa zerada de setembro a dezembro, MDR e antecipação; remessa segue normal. | FINANCEIRO | #5 | |
| RN-12 | Casa: o que a Orbe cobrou é **devolução nossa** (concessão do comercial fora do contrato), separada das divergências de contrato e **fora da cobrança da Orbe**. | FINANCEIRO | #5, #14, #21, #27, #30 | Pode listar as linhas em divergências se rotuladas como isenção (#21, #30). |
| RN-13 | A devolução à Casa é o valor **descontado de fato** (`valor_taxa`): R$ 15.396,77, e não a fórmula (R$ 15.397,42). | FINANCEIRO | #33 | |
| RN-14 | A isenção da antecipação vale pela **data da antecipação**, sem procurar as vendas de origem. | FINANCEIRO | #35 | |
| RN-15 | "Setembro a dezembro" da Casa = de **01/09/2026 a 31/12/2026**, confirmado pela Helena (T-800, item 8). A volta à planilha em 2027 é decisão do comercial (**N3**). | FINANCEIRO | P2, P14 | N3 (comercial) |
| RN-16 | A taxa de uma **venda** vale pela data da venda (ex.: aditivo da Bridge "a partir de 15/09"). | FINANCEIRO | P3 | resposta ao T-800 (9) |
| RN-17 | **Atlas** sem contrato: não fatura, vira pendência, e o **repasse segue normal**. | FINANCEIRO | #2, #24, #28, #29 | |
| RN-18 | Atlas: quando o comercial confirmar, a taxa vale **desde 10/09** e o fechamento de outubro puxa as linhas de setembro. | FINANCEIRO | #16 | |
| RN-19 | O CNPJ da aba de 2025 pode **identificar** a Atlas; a taxa daquela aba não vale. | FINANCEIRO | #29 | |
| RN-20 | Atlas fica **fora** de `comissoes_por_lojista.csv`, com pendência (e não zerada). | TIME | #28, #29 | Helena aceita as duas formas; "escolham uma e registrem no HIPOTESES.md". |
| RN-21 | Os três ECs sem cadastro são a Novo Horizonte Intercâmbio (1043300981), a Horizonte Viagens e Turismo (1043396662) e a Kiwi Experience (1038867654). | FINANCEIRO | #2 | |
| RN-22 | A Tarvo não vende acima de 12 parcelas; se aparecer, é pendência. | FINANCEIRO | #23 | |
| RN-23 | Estorno com bandeira diferente da venda: segue o vínculo pela referência, **sem contestar nem abrir pendência**. | FINANCEIRO | #37 | |
| RN-24 | **Fluente**: o Pix a 0,79% é condição negociada (T-800, item 7). Fica como está na planilha, sem pendência. A pendência de R$ 9,16 foi retirada, porque a nota já usava 0,79%. | FINANCEIRO | P15 | resposta ao T-800 (7) |
| RN-25 | O **alerta de antecipação** (critério) é do time; ele vai para a Helena e o comercial e **não muda nenhum número**. | TIME | #14, #27, #30, #32 | O destinatário do alerta é FINANCEIRO (#14). Critério atual: R32 do `HIPOTESES.md`. |
| RN-26 | Orbe cobrando **abaixo** do contrato também é divergência; a Helena decide caso a caso. Não ocorreu em setembro. | FINANCEIRO | #14 | |
| RN-27 | **Ajustes tardios da Orbe** (arquivo 06): entram no mês do movimento se chegarem antes da aprovação; depois, no mês seguinte. | FINANCEIRO | #36 | Confirma a P13 (resolve a pergunta 7 antiga). |
| RN-28 | Ajuste tardio com **o mesmo id** de uma linha do relatório: o critério é do time, com pendência para a Helena. Nunca aconteceu. | TIME | #36 | Critério ainda **não escrito** no `HIPOTESES.md`. |
| RN-29 | Comissão **negativa** (Casa, −R$ 5,50) fica em `comissoes_por_lojista.csv` com o valor real e vira pendência; não emite nota. | TIME | #28, P17 | Helena: "se aparece com zero ou fica fora é com vocês". |

## 2. Remessa

| id | Regra | MTD_INFERENCIA | Base | Observação |
|---|---|---|---|---|
| RN-30 | A comissão é **50% do "Spread R$" realizado** da Ponte. | FINANCEIRO | #4 | |
| RN-31 | Spread em branco ou "padrão" na planilha = **1,5% sobre a PTAX** de referência. | FINANCEIRO | #4 | |
| RN-32 | Os 50% são arredondados **por operação** (R$ 131,005 vira R$ 131,01). | FINANCEIRO | #7 | |
| RN-33 | **Spread negativo**: não se aceita; fica fora da comissão e da nota, e a Helena contesta. | FINANCEIRO | #4 | |
| RN-34 | Spread negativo é **pendência de contestação**, não divergência (o lojista não pagou a mais). Listar em divergências é opcional, se ficar claro que é outra natureza. | FINANCEIRO | #13 | |
| RN-35 | A pendência do spread negativo traz **os dois valores, rotulados**: o do relatório e a diferença até o spread do contrato. | FINANCEIRO | #27 | |
| RN-36 | **Operação repetida**: o número da operação é único; conta-se uma vez. | FINANCEIRO | #4 | A frase dela é "o número da operação é único"; "conta uma vez" é leitura nossa. |
| RN-37 | "Aprovado c/ ressalva" não muda nada. | FINANCEIRO | #4 | |
| RN-38 | Vale a **data de contratação**, não a de liquidação. | FINANCEIRO | #4 | |
| RN-39 | Divergência de remessa = o lojista pagou spread diferente do contratado (ex.: Mundo Aberto, 1,20% desde julho). O valor é o **cheio**, não os 50%. | FINANCEIRO | #4, #6, #14 | |
| RN-40 | A fórmula da divergência usa o **Spread R$ realizado** (R$ 1.418,88 na Mundo Aberto), e não o `spread_pct` (R$ 1.418,85). | TIME | #23 | Helena: "são três centavos, escolham um critério e escrevam qual". |
| RN-41 | **Tolerância** de 0,005 p.p. para considerar o spread como contratado. | TIME | #6, #7 | Em `config/parametros.csv`. |
| RN-42 | A nota da Ponte sai pelo **realizado**, inclusive o excesso da Mundo Aberto. A contestação é à parte; se a Ponte devolver, a nossa metade sai no mês do ajuste. | FINANCEIRO | #9 | |
| RN-43 | **Ajuste da Ponte**: linha nova com Nº de operação próprio, Spread R$ negativo e observação "AJUSTE REF PC-…". Entra no mês em que aparece e abate a participação do mês, dentro da nota única; o rastro aponta para a operação original; sem nota complementar. | FINANCEIRO | #26, #28 | |
| RN-44 | Não contar que a Ponte descontará algo do repasse. Conferir o TED quando cair é pendência boa. | FINANCEIRO | #10 | |
| RN-45 | Operação de **CNPJ fora da planilha**: calcular a nossa metade mesmo assim e abrir pendência de cadastro para o comercial. Registrar como premissa. | TIME | #15 | Não ocorreu em setembro. |
| RN-46 | O PIX de R$ 18.240,00 é dinheiro de uma remessa que sai em outubro e fica em **recursos para remessas**. A Ponte Aérea Estudantil é lojista, sem relação com a Ponte Câmbio. | FINANCEIRO | #14, #15, #34 | |
| RN-47 | A contestação à Ponte está **dentro do prazo**, segundo a Helena (T-800, 1). O e-mail da Ponte deu 5 dias úteis a partir de 02/10 (09/10). **Decisão nossa:** a contestação só é enviada com a data confirmada por escrito pela Ponte. | FINANCEIRO | R18 | **N1** |
| RN-48 | A contestação sai como **rascunho de e-mail por contraparte**, com as operações anexadas; a Helena revisa e envia. | FINANCEIRO | #18 | |

## 3. Notas e pendências

| id | Regra | MTD_INFERENCIA | Base | Observação |
|---|---|---|---|---|
| RN-50 | **Checkout**: uma nota por lojista por mês, no valor da comissão do mês pela taxa contratada. | FINANCEIRO | #3 | |
| RN-51 | **Zero ou negativo não emite nota**; o negativo não passa para o mês seguinte automaticamente; vira pendência para a Helena. | FINANCEIRO | #3, #26, #28 | |
| RN-52 | **Remessa**: uma nota só, com a Ponte Câmbio como tomadora, pelo total da participação do mês. Não há nota por lojista. | FINANCEIRO | #3 | |
| RN-53 | Não existe texto padrão: basta o serviço e a competência. | FINANCEIRO | #3 | O texto usado hoje é escolha nossa. |
| RN-54 | A nota só documenta a taxa que a Orbe já descontou; não gera cobrança nova. | FINANCEIRO | #20 | |
| RN-55 | Razão social do tomador: usar o **nome da planilha** com o CNPJ; a Bia confere na emissão. | FINANCEIRO | | resposta ao T-800 (4) |
| RN-56 | CNPJ sempre com **14 dígitos**; o zero à esquerda se perdeu na planilha (Fluente, Campus Global). | FINANCEIRO | P11 | resposta ao T-800 (5) |
| RN-57 | **Sem retenção** de ISS ou IRRF pela Ponte; o ISS da nota vai no DAMSP do mês seguinte, fora deste fechamento. | FINANCEIRO | | resposta ao T-800 (6) |
| RN-58 | **Taxa e condição comercial**: aprova o comercial, e a Helena registra. **Regra de como fechar**: aprova a Helena. Registrar quem aprovou e quando. | FINANCEIRO | #19 | |
| RN-59 | Decisão de cadastro e contrato é do **comercial**; a Bia mantém a planilha, mas não decide taxa. | FINANCEIRO | #23 | |
| RN-60 | Pendência de contestação: **uma por contraparte e por lojista**, com o detalhe das transações anexado. | FINANCEIRO | #23 | As pendências de spread negativo estão **por operação**; ver aviso no relatório. |
| RN-61 | Faltou fonte ou informação: **fecha o que não depende**, marca o provisório e o bloqueado, e a Helena libera. Taxa e cadastro, o comercial decide antes. | FINANCEIRO | #31 | |
| RN-62 | A estrutura dos arquivos é a mesma todo mês; se o layout mudar, a solução deve **avisar** em vez de quebrar calada. | FINANCEIRO | #31 | |

## 4. Bancos e classificação

### Critérios

| id | Regra | MTD_INFERENCIA | Base |
|---|---|---|---|
| RN-63 | `conta_codigo` é a **contrapartida** do movimento no banco. Se o valor já estava registrado, o pagamento ou recebimento **baixa a conta onde estava**. | FINANCEIRO | #8 |
| RN-64 | Folha, ISS, INSS, FGTS e DARFs de agosto pagos em setembro **já estavam provisionados**; todo mês a folha e os impostos do mês ficam provisionados, e o pagamento do mês seguinte baixa a provisão. | FINANCEIRO | #5, #8, #17 |
| RN-65 | O repasse da Ponte de 04/09 é o **spread de agosto**, já registrado como comissão a receber. | FINANCEIRO | #5, #8 |
| RN-66 | Fora isso, **nada estava provisionado**: tarifas, aluguel, cloud, assinaturas e serviços vão direto para a despesa do mês. | FINANCEIRO | #8 |
| RN-67 | Quando o extrato não deixar claro, **declarar a premissa** no `HIPOTESES.md` e seguir. | FINANCEIRO | #8 |
| RN-68 | A provisão de setembro **não** é do fechamento: quem faz é a contabilidade. O fechamento classifica o que passou nos extratos. | FINANCEIRO | #30 |
| RN-69 | Os créditos da Orbe são classificados; conciliar parcela por parcela **não** é necessário neste fechamento. | FINANCEIRO | #11 |
| RN-70 | A Orbe deposita tudo no Aurora. Débito e Pix caem no dia seguinte; crédito e parcelado, ao longo dos meses. O saldo negativo do Aurora é a **conta garantida**. | FINANCEIRO | #11 |
| RN-71 | O repasse é feito duas vezes por mês (perto dos dias 10 e 24), do que a Orbe já liquidou. Na prática, pode ser pago antes pela conta garantida, sem limite escrito. | FINANCEIRO | #20, #22 |
| RN-72 | O PIX de R$ 7.350,00 sem identificação **não é receita** até alguém identificar. | FINANCEIRO | #5 |
| RN-73 | A devolução de R$ 12.400,00 é um PIX de repasse que voltou, com motivo desconhecido; `2.1.01.001` ou `2.1.01.002` servem, desde que o critério seja o mesmo e o motivo escrito. | FINANCEIRO | #5, #17 |
| RN-74 | A transferência de R$ 300.000,00 saiu do Aurora em 30/09 e cai no Meridiano em 01/10; o tratamento é do time. | FINANCEIRO | #5 |

### Regra por regra do `src/classificacao.py`

Helena disse duas vezes que **não valida conta por conta** (#23, #24). Por isso a coluna `MTD_INFERENCIA` olha para o que sustenta a escolha da conta: a resposta dela (FINANCEIRO), a delegação ou o mapeamento de referência do brief (TIME), ou só a minha leitura da descrição (IA).

| Regra | Descrição do extrato | Conta | MTD_INFERENCIA | O que sustenta |
|---|---|---|---|---|
| A01_ORBE | TED recebida da Orbe | 1.1.03.001 | TIME | #11 ("os créditos da Orbe vocês classificam") e RN-63 |
| A02_CONTABILIDADE | PIX enviado a "contabilidade" | 4.2.06 | TIME | Referência do brief (L53); RN-66 (serviços) |
| A03_REPASSE | PIX enviado (qualquer) | 2.1.01.001 | FINANCEIRO | Resposta ao T-800 (9): em setembro, o único PIX enviado que não é repasse é o da contabilidade (A02). Para quem não é lojista, a premissa serve. |
| A04_TRANSFERENCIA | Transferência entre contas | 1.1.09.001 | TIME | #5: "o que fazer é decisão sua" |
| A05_FOLHA | Pagamento de salários | 2.1.04.001 | FINANCEIRO | RN-64; a conta é a homônima do plano e foi o exemplo da própria pergunta #8 |
| A06_INSS | GPS INSS | 2.1.04.002 | FINANCEIRO | RN-64 |
| A07_FGTS | GRF FGTS | 2.1.04.003 | FINANCEIRO | RN-64 |
| A08_ISS | Pagamento de ISS | 2.1.03.003 | FINANCEIRO | RN-64 |
| A09_DARF_IRRF | DARF 0561 | 2.1.03.004 | FINANCEIRO | RN-64: "os DARFs são de agosto" |
| A10_DARF_PIS | DARF 8109 | 2.1.03.001 | FINANCEIRO | RN-64 |
| A11_DARF_COFINS | DARF 2172 | 2.1.03.002 | FINANCEIRO | RN-64 |
| A12_CONDOMINIO | Boleto de condomínio | 4.2.02 | TIME | Referência (L16); RN-66 (aluguel) |
| A13_AWS | Amazon Web Services | 4.2.03 | TIME | Referência (L47); RN-66 (cloud) |
| A14_GOOGLE | Google Workspace | 4.2.04 | TIME | Premissa do brief (L48); RN-66 (assinaturas) |
| A15_TARIFA | Tarifa bancária (Aurora) | 4.2.01 | TIME | Referência (L10, L90); RN-66 (tarifas) |
| A16_PIX_SEM_ID | PIX recebido sem identificação | 1.1.09.002 | TIME | RN-72 é FINANCEIRO; a conta é referência (L50) |
| A17_DEVOLUCAO | Devolução de PIX | 2.1.01.001 | TIME | RN-73: escolher uma conta e escrever o motivo |
| M01_PIX_LOJISTA | PIX recebido de lojista | 2.1.02.001 | TIME | #34 ("fica em recursos para remessas") vale para o PIX de R$ 18.240; o resto segue o mesmo critério |
| M02_TED_PONTE | TED enviada à Ponte (liquidação) | 2.1.02.001 | FINANCEIRO | Princípio confirmado (T-800, 8 e 9): recurso de lojista fica no passivo. A conta é critério nosso (**N9**) |
| M03_TRANSFERENCIA | TED recebida da própria Tarvo | 1.1.09.001 | TIME | #5: tratamento é do time |
| M04_COMISSAO_PONTE | TED de repasse de comissão da Ponte | 1.1.03.002 | FINANCEIRO | RN-65: "já estava como comissão a receber" |
| M05_CDB | Aplicação ou resgate automático | 1.1.02.001 | FINANCEIRO | Princípio confirmado (T-800, 8 e 9): aplicação não tem efeito no resultado. A conta é critério nosso (**N9**) |
| M06_RENDIMENTO | Rendimento de aplicação | 3.2.01 | FINANCEIRO | Resposta ao T-800 (10): receita do mês |
| M07_TARIFA | Tarifa bancária (Meridiano) | 4.2.01 | TIME | Referência; RN-66 |
| M08_SEGURO | Seguro empresarial | 4.2.05 | FINANCEIRO | Resposta ao T-800 (10): despesa do mês, como assinatura. A conta 4.2.05 segue em **N8** |
| M09_IOF | IOF s/ operação de crédito | 4.3.01 | TIME | Resposta ao T-800 (2): a operação é do Meridiano e a conta é decisão nossa |

---

## 5. Regras do edital e da organização (sem `MTD_INFERENCIA`)

| Regra | Fonte |
|---|---|
| Duas linhas de negócio. Checkout: a Tarvo ganha a taxa (MDR) e a de antecipação. Remessa: ganha participação no spread. | Edital |
| Todo número da saída aponta para a linha de origem; total que não fecha com a soma das linhas conta como número inventado. | Edital |
| `ref_origem`: `id_transacao` (Orbe), Nº Operação (Ponte), linha física no Aurora (L10, L11…), FITID no Meridiano. | Edital |
| Formato: `;` como separador, ponto decimal, datas AAAA-MM-DD, CNPJ com 14 dígitos; colunas extras são bem-vindas. | Edital |
| Onde faltar resposta, assumir, escrever a premissa e seguir. | Edital |
| Não há pacote de outubro; "rodar em outubro" é servir para arquivos novos no mesmo formato, sem mexer no código. A `saida/` tem só setembro. | #25 (organização) |
| `quem_decide` é texto livre; vários `ref_origem` na mesma célula, separados por `\|`, valem; pendência de acompanhamento com motivo e próximo passo não é alarme falso. | #25 (organização) |
| Rastro mínimo no formato das instruções; ajuda ter rastro de divergências e da nota da Ponte, registro de cada execução e a regra aplicada em cada linha. | #38 (organização) |

---

## 6. Resumo

Contagem feita sobre as tabelas das seções 1 a 4.

| MTD_INFERENCIA | Regras de negócio e critérios (RN) | Contas da classificação (A e M) | Total |
|---|---|---|---|
| FINANCEIRO | 66 | 13 | 79 |
| TIME | 7 | 13 | 20 |
| IA | 0 | 0 | 0 |

Não sobra suposição **IA** aberta: a rodada 2 (N1 a N10) foi respondida em 17/10 e está fechada em `HIPOTESES.md`, seção 3. As contas TIME são critério nosso, registrado com o motivo; a Helena disse que não confere conta por conta.
