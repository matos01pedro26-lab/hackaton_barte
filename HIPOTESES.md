# Hipóteses, regras e perguntas — fechamento Tarvo set/2026

Este arquivo separa três coisas: o que o financeiro **confirmou**, o que eu **assumi** para seguir, e o que ainda está **em aberto**. Cada item de premissa diz o que muda se estiver errado.

---

## 1. Regras confirmadas pelo financeiro

Fonte: respostas do @manuel.freitas e da Helena (financeiro) no canal `#tarvo-financeiro`, a partir do texto colado pelo time.

| # | Regra | Efeito no cálculo |
|---|---|---|
| R1 | **Checkout é faturado pela taxa contratada**: `valor bruto × taxa da planilha`, não pelo valor cobrado pela Orbe. | A comissão sai da planilha. A Orbe vira base de comparação para as divergências. |
| R2 | **Estorno de mês anterior abate a comissão do mês do estorno**, usando a taxa válida na **data da venda original**. | O estorno entra com sinal negativo no mês dele, pela taxa da data da venda. |
| R3 | **Atlas (EC 1076801732) não é faturada** até confirmação do comercial. A Helena confirmou: começou a transacionar em 10/09, não tem contrato assinado na aba vigente, e a aba "ANTIGO 2025" não vale para ela. | Fora da comissão e da nota. Vira pendência para o comercial. Não se calcula divergência, porque não há taxa contratada. |
| R4 | **Checkout: uma nota por lojista por mês**, somando vendas e antecipações e abatendo estornos e reversões (Manuel: "abatendo ou somando conforme o caso"). | Um total por lojista, não por transação. |
| R5 | **Remessa: Ponte Câmbio é a tomadora única**, pelo total da participação. Não há nota por lojista na remessa. | Uma nota só, para a Ponte. |
| R6 | **Comissão de remessa = 50% do spread realizado.** | Já estava no e-mail da Ponte; confirmado. |
| R7 | **Spread negativo fica fora da comissão e da nota.** | 4 operações excluídas. |
| R8 | **Arredondamento comum (meio para cima), por operação.** | Vale para comissões calculadas por nós. Não corrige o truncamento da Orbe. |
| R9 | **Plano de contas registra a contrapartida** dos movimentos bancários. | Cada classificação de extrato precisa do lado oposto (partida dobrada). |
| R10 | **Divergências de remessa viram pendência de contestação com a Ponte.** | Prazo de resposta: 5 dias úteis (e-mail de 02/10 — já passou). |
| R11 | **Entrega: um repositório por time, até 18h30**, com código, pasta de saída, prompts e links de plataformas. O README tem que permitir rodar o fechamento **do zero**. | Estrutura do repositório. |
| R12 | **A banca executa a solução e compara o resultado com a pasta de saída** do repositório. | A execução tem que ser determinística: dependências fixadas, ordenação estável, IA com resposta em cache ou desligável. |
| R13 | **Antecipação entra na nota do lojista** pela taxa contratada (2,10%). Reversão de antecipação abate. | Era a P1. Confirmado pelo Manuel. |
| R14 | **Diferença de centavos causada pelo truncamento da Orbe é desconsiderada.** | Era a P2. A comparação é pelo percentual (taxa aplicada × contratada), então essas diferenças nem aparecem. |
| R15 | **Divergência de checkout = `valor bruto × (taxa aplicada − taxa contratada)`.** | Positiva = Orbe cobrou a mais. No estorno o sinal se inverte. |
| R16 | **Remessa fatura pelo spread realizado da Ponte mesmo quando ele diverge do contratado.** | Era a P5. O Mundo Aberto fatura a 1,50%, e a diferença para 1,20% vai para divergência e contestação (R10). |
| R17 | **Divergência de remessa = valor cheio** (não os 50%), pela taxa aplicada × a contratada. O spread contratado é **sobre a PTAX de referência**. | Divergência R$ = `Valor ME × PTAX × (spread aplicado % − spread contratado %)`. |
| R18 | **Spread em branco ou "padrão" na planilha = 1,5% sobre a PTAX de referência.** | Era a P8. Vale para Kiwi, Canguru, Ponte Aérea e demais com a célula vazia. |
| R19 | **Mapeamento de ECs (Helena)**: `1043300981` (HORIZONTE INTERCAMBIO) = linha "Novo Horizonte Intercambio"; `1043396662` (HORIZONTE VIAGENS TURISMO) = linha "Horizonte Viagens" (são duas empresas diferentes); `1038867654` (KIWI EXPERIENCE TURISMO) = linha "Kiwi Experience". O CNPJ e as taxas vêm da linha de cada um na aba vigente. | Registrado em `config/mapeamento_ec.csv` (status `CONFIRMADO`). Os três entram na comissão: 233 linhas, cerca de R$ 27,5 mil. Com as taxas da aba vigente, nenhum deles tem divergência. |
| R20 | **Pagamentos de folha, tributos e repasses de agosto já estavam provisionados**: em setembro eles baixam o passivo (ou o recebível) correspondente e não são despesa do mês. | Folha 08, INSS, FGTS, ISS, IRRF, PIS, COFINS e PIX de repasse vão contra contas do grupo 2.1. |
| R21 | **Tarifas, aluguel/condomínio, cloud e similares entram direto como despesa do mês.** | Contas do grupo 4.2. |
| R22 | **Os depósitos da Orbe caem integralmente na Aurora.** | Todo TED da Orbe baixa `1.1.03.001 Recebíveis de adquirente - Orbe`. |
| R23 | **O saldo negativo da Aurora é a conta garantida**, usada para pagar lojistas antecipadamente. | Não é erro nem falta de lançamento. O plano não tem conta de passivo para isso, então o saldo fica credor na própria `1.1.01.001`. |
| R24 | **Casa do Estudante tem tarifa zerada no checkout de setembro a dezembro/2026** (MDR e antecipação), por acordo do comercial. A Orbe cobrou sem saber: o valor cobrado é divergência, e a Helena devolve. Estorno de venda anterior a setembro usa a taxa da planilha. Fonte: Helena, conforme o `HIPOTESES.md` da branch `remessa` (commit `d9810f5`). | Registrado em `config/condicoes_especiais.csv`. A comissão da Casa cai de R$ 15.391,92 (pela planilha) para −R$ 5,50, porque sobra só o estorno `TX88445133` (débito de venda de 21/08, a 1,49%). Saldo negativo não emite nota e vira pendência para a Helena. |
| R25 | **Repasse a lojista, pela regra, é só do que a Orbe já liquidou.** Na prática, quando um lojista pressiona, a Bia às vezes paga antes de a Orbe liquidar, usando a conta garantida da Aurora. Isso não está escrito em lugar nenhum e não tem limite. Fonte: Helena, resposta à Turma do Barulho no #tarvo-financeiro (17/10, 10h59). | Não muda a classificação: o PIX de repasse continua baixando `2.1.01.001`, porque a obrigação com o lojista existe desde a venda. Explica por que os repasses (R$ 4,23 mi) superam os TEDs da Orbe (R$ 3,56 mi) e por que a Aurora fica negativa (R23). Sem a regra de liquidação da Orbe, não dá para dizer quais PIX foram antecipados. |

---

## 2. Premissas que eu assumi

Estas não estão confirmadas. Se alguma estiver errada, o número muda na direção indicada. As premissas P1, P2, P5 e P8 viraram regras (R13, R14, R16 e R18).

| # | Premissa | Por quê | Se estiver errada |
|---|---|---|---|
| P3 | **Vigência usa a data do movimento** nas vendas, e a **data da venda original** nos estornos. | R2 diz isso só para estornos. | Afeta a Bridge (muda em 15/09). Na prévia, 5 vendas de 15–17/09 aparecem a 2,59% em vez de 2,19%. |
| P4 | **EC sem mapeamento confirmado fica fora da comissão**, em grupo próprio, como pendência. Em setembro, só a Atlas (R3). | Casar por nome é proibido pelo brief. | Vale para EC novo em outubro: entra só depois de uma linha em `config/mapeamento_ec.csv`. |
| P6 | **Operação "APROVADO C/ RESSALVA" entra na comissão e na nota.** | Manuel: "seguem normalmente para liquidação". | 16 operações, spread R$ 4.829,37. |
| P7 | **Operação repetida na Ponte conta uma vez.** `PC-0926-0162` aparece duas vezes, a segunda marcada "reprocessada". | Mesmos campos, mesmo valor e data. **O banco confirma**: os 21 TEDs para a Ponte somam, ao centavo, as 232 operações únicas (Valor R$ + IOF), então a cópia não foi paga. | O Resumo soma R$ 821,88 a mais. |
| P9 | **Linha do relatório da Ponte que não é operação de câmbio (ex.: crédito ou débito de ajuste) vira pendência**, fora da comissão e da nota. | O formato do ajuste não está nos dados de setembro; tratar como operação normal poderia faturar um valor errado. | Se o formato for conhecido e a regra clara, vira lançamento e deixa de ser pendência. |
| P10 | **Operação de spread negativo não entra em `divergencias_taxa`**: já é pendência de contestação (R7, R10). | Evita contar o mesmo problema duas vezes. | As 4 operações apareceriam também como divergência. |
| P11 | **Classificação contábil dos extratos** segue o mapa da seção 2.1. | Aplica R20 a R23 ao plano Fênix, só em contas analíticas. | Muda a conta de contrapartida, não o valor. |
| P12 | **Comissão de checkout zero ou negativa fica em `comissoes_por_lojista` com o valor real** e vira pendência `COMISSAO_NAO_POSITIVA` (não emite nota). Em setembro, só a Casa do Estudante (−R$ 5,50, R24). | O número precisa fechar com o rastro; a regra de não emitir é da nota, não da comissão. | Se o gabarito tirar a linha, o total de checkout sobe R$ 5,50 e a Casa sai do arquivo. |
| P13 | **`id_saida` do checkout**: `CHK-AAAA-MM-<cnpj>` para comissão e `PEN-CHK-AAAA-MM-<tipo>-<ref>` para pendência. | Determinístico e legível; a consolidação com remessa e bancos ainda não definiu um padrão comum. | Só muda o identificador, não os valores. |
| P14 | **Valor da pendência = o que está em jogo**: EC retido = soma do bruto (não há taxa contratada); cadastro de EC = comissão que depende do mapeamento em `config/`; condição especial = comissão que a planilha cobraria; sem taxa = bruto da transação. | Dá ao financeiro o tamanho de cada decisão, sempre com rastro até as transações. | Só muda a coluna `valor_brl` de `pendencias.csv`. |

### Detalhe da P9 (contribuição do Gabriel, commit `90d0d6b`; era a "P1" do arquivo dele)

- **Status:** premissa (não confirmada).
- **Contexto:** a Helena disse que a Ponte comunica o resultado de uma contestação por e-mail e envia o ajuste no relatório do mês seguinte, como crédito ou débito, e que ela registra o ajuste no fechamento do mês em que ele aparece. O relatório de setembro não tem nenhuma linha assim, então o formato dessas linhas é desconhecido.
- **Decisão:** no fechamento de outubro, qualquer linha do relatório da Ponte que não seja uma operação de câmbio normal (por exemplo, crédito ou débito de ajuste) não entra na comissão nem na nota. Ela vira pendência em `pendencias.csv`, com valor e motivo, para a Helena decidir.
- **Por quê:** o formato do ajuste não está nos dados. Tratar uma linha desconhecida como operação normal poderia faturar um valor errado. Parar e pedir decisão é a opção mais segura, e a Helena já pediu pendência para o que foge da regra.
- **Origem:** resposta 6 à pergunta da Turma do Barulho (canal #tarvo-financeiro, 17/10).
- **Relação com R10:** a contestação de divergências de remessa com a Ponte (R10) é o que gera esses ajustes no mês seguinte.

### 2.1 Mapa de classificação contábil dos extratos (P11)

Contrapartida da conta bancária (`1.1.01.001` Aurora ou `1.1.01.002` Meridiano).

| Lançamento no extrato | Conta de contrapartida | Base |
|---|---|---|
| TED RECEBIDA … ORBE ADQUIRENCIA (Aurora) | 1.1.03.001 Recebíveis de adquirente - Orbe | R22 |
| PIX ENVIADO <lojista> (Aurora) | 2.1.01.001 Repasses a lojistas a pagar | R20 |
| PIX ENVIADO CONTABILIDADE EXATA | 4.2.06 Serviços contábeis e jurídicos | R21 |
| PAGTO SALARIOS – FOLHA 08/2026 | 2.1.04.001 Salários a pagar | R20 |
| GPS INSS 08/2026 · GRF FGTS 08/2026 | 2.1.04.002 · 2.1.04.003 | R20 |
| PAGTO ISS 08/2026 · DARF 0561 IRRF · DARF 8109 PIS · DARF 2172 COFINS | 2.1.03.003 · 2.1.03.004 · 2.1.03.001 · 2.1.03.002 | R20 |
| TAR PACOTE · TAR TED/PIX · TARIFA MANUTENCAO · TARIFA PACOTE CAMBIO | 4.2.01 Tarifas bancárias | R21 |
| BOLETO CONDOMINIO | 4.2.02 Aluguel e condomínio | R21 |
| DEB AUT AMAZON WEB SERVICES | 4.2.03 Cloud e infraestrutura | R21 |
| CARTAO PJ – GOOGLE WORKSPACE | 4.2.04 Softwares e assinaturas | R21 |
| SEGURO EMPRESARIAL PARC 09/12 | 4.2.05 Seguros | R21 |
| IOF S/ OPERACAO CREDITO | 4.3.01 IOF | R21 |
| TRANSF ENTRE CONTAS (Aurora) ↔ TED … MESMA TITULARIDADE (Meridiano) | 1.1.09.001 Transferências entre contas próprias | premissa |
| PIX RECEB <lojista> (Meridiano) | 2.1.02.001 Recursos de lojistas para remessas a liquidar | premissa |
| TED ENVIADA PONTE CAMBIO … LIQ OPERACOES | 2.1.02.001 (baixa) | premissa |
| TED RECEB PONTE CAMBIO … REPASSE COMISSAO 08/2026 | 1.1.03.002 Comissões de intermediação a receber - câmbio (baixa) | R20 |
| APLICACAO / RESGATE AUTOMATICO CDB DI | 1.1.02.001 Aplicação automática Meridiano | premissa |
| RENDIMENTO APLIC AUTOMATICA | 3.2.01 Rendimentos de aplicações | premissa |
| PIX RECEBIDO … SEM IDENTIFICACAO (R$ 7.350) | 1.1.09.002 Créditos não identificados + pendência | premissa |

---

## 3. Perguntas em aberto para o financeiro

Ordenadas por impacto no número. Antes de perguntar, confirme se a resposta já não está no canal. Já respondidas: mapeamento dos ECs (R19), Aurora negativa (R23), spread "padrão" (R18).

1. **Rota Global (EC 1074504011)**: desde 12/09, todas as 87 linhas de crédito saem com +0,50 p.p. sobre o contrato (prévia: R$ 1.644,28 de vendas, −R$ 98,42 de estornos). É erro da Orbe ou condição nova? Se for erro, o valor vira devolução ao lojista ou só contestação?
2. **Bridge**: confirme que a vigência das vendas segue a data do movimento (P3). Hoje, 5 vendas de 15–17/09 saem a 2,59% em vez de 2,19% (prévia: R$ 29,94).
3. **Mundo Aberto**: 1,20% (planilha, "spread negociado em jul/26") ou 1,50% (Ponte, 23 operações)? A comissão já usa o realizado (R16). A pergunta é se a diferença vai para contestação com a Ponte (R10) ou se a planilha está desatualizada.
4. **Atlas (EC 1076801732)**: a Aurora pagou R$ 249.301,77 em 2 PIX para a Atlas em setembro, e não há faturamento (R3). É adiantamento, pagamento de outro serviço ou erro? Qual o contrato?
5. **Spreads negativos (4 operações, R$ −1.834,05)**: a observação diz "taxa travada no pedido (D-1)". Quem absorve o prejuízo — Tarvo ou Ponte? É caso de contestação (R10) ou aceite?
6. **Saída de R$ 300.000 da Aurora em 30/09** (L92) para o Meridiano: não aparece no OFX. Está em trânsito? Entra em outubro?
7. **Estornos de vendas de agosto** (9 linhas na Orbe, sem origem em setembro): a comissão deles é do mês do estorno (R2), mas a taxa de origem está nas linhas de agosto, que não temos. Confirmar que a taxa vem da planilha vigente em agosto, ou pedir o relatório de agosto.
8. **Divergências de taxa da Orbe**: o lojista pode ser cobrado a mais? Se sim, quem devolve (Tarvo ou Orbe)?
9. **DEVOLUCAO PIX – MUNDO ABERTO (R$ 12.400, Aurora 23/09)**: é um repasse devolvido? Volta para `2.1.01.001` ou vai para `2.1.01.002`?
10. **Notas fiscais**: regime tributário, retenções e código de serviço.

### 3.1 Pendências de cadastro com o financeiro

São dados que pertencem à planilha de taxas, mantida pelo financeiro, e que só conseguimos perguntando. A solução aplica a resposta por `config/`, mas a planilha continua incompleta. Por isso cada item fica **pendente para o financeiro** até a planilha ser corrigida. A coluna `pendencia_financeiro` dos arquivos de `config/` diz o que corrigir e vai alimentar o `pendencias.csv`. Depois da correção na planilha, a linha correspondente em `config/` pode sair.

| Item | O que falta na planilha | Configuração usada hoje | Base |
|---|---|---|---|
| Kiwi Experience | EC Orbe `1038867654` na linha 9 (obs "EC pendente") | `config/mapeamento_ec.csv` | R19 |
| Horizonte Viagens | EC Orbe `1043396662` na linha 8 | `config/mapeamento_ec.csv` | R19 |
| Novo Horizonte Intercambio | EC Orbe `1043300981` na linha 28 | `config/mapeamento_ec.csv` | R19 |
| Casa do Estudante | Taxa zerada de 01/09 a 31/12/2026; a linha 13 só tem o comentário "conversar com Diego (comercial) sobre condição especial" | `config/condicoes_especiais.csv` | R24 |

---

## 4. Achados que mudam número

Números da prévia v2 (notebook `exploracao_inicial.ipynb`, seção 10). São prévias: dependem das premissas acima e não passaram pelo financeiro.

- **Checkout (mapeados)**: R$ 194.943,54 de comissão em 18 lojistas (MDR + antecipação), com 1.653 linhas. **Ainda sem os três ECs da R19**, que somam 233 linhas e cerca de R$ 27,5 mil (Kiwi R$ 10,7 mil, Horizonte Viagens R$ 9,0 mil, Novo Horizonte R$ 7,8 mil), sem divergência de taxa.
- **Checkout calculado por `src/checkouts` (R1, R2, R8, R13, R19, R24)**: **R$ 207.039,73 em 21 lojistas**, 1.886 linhas no rastro e 57 da Atlas retidas (R3). Bate com uma prévia independente feita antes do código. A diferença para a prévia de R$ 222.437,15 do `analise_exploratoria.ipynb` é a tarifa zerada da Casa do Estudante (R$ 15.397,42 dispensados). São 6 pendências: 4 de cadastro para o financeiro (seção 3.1), Casa negativa (P12) e Atlas (comercial).
- **Divergências reais de taxa**: 92 linhas, soma R$ 1.575,80 cobrados a mais pela Orbe. Quase tudo é Rota Global (R$ 1.545,86 líquidos) e Bridge (R$ 29,94).
- **Arredondamento**: 1.561 linhas batem dentro de R$ 0,01 e ficam fora das divergências (R14).
- **Remessa**: comissão de R$ 39.543,45 para a nota única da Ponte, com 4 spreads negativos fora (R7) e a duplicata contada uma vez (P7).
- **Ponte — contestação**: só o Mundo Aberto tem spread realizado diferente do contratado.
- **Atlas**: 57 linhas de checkout retidas (R3), com R$ 262.138,61 de bruto. Mas a Aurora já pagou R$ 249 mil, então há pagamento sem nota. A Orbe aplicou 1,99 / 3,49 / 3,99 / 4,49 / 0,99%, taxas que não estão em nenhuma das abas.
- **Novo Horizonte**: o CNPJ (66.564.512/0001-99) já estava mapeado na remessa, e o EC de checkout (1043300981) passou a ter mapeamento pela R19. Os dois status agora batem.

- **Remessa fecha com o banco**: cada um dos 21 TEDs para a Ponte é a soma de (Valor R$ + IOF) das operações do mesmo dia, e o PIX de cada lojista no Meridiano é a soma das suas operações (13 de 14 lojistas exatos). A exceção é um PIX **redondo de R$ 18.240,00** da Ponte Aérea em 17/09, sem operação correspondente: pendência.
- **Checkout não fecha com o banco**: os TEDs da Orbe (R$ 3.557.246,29) não seguem nenhuma regra simples do relatório. Os repasses a lojistas (R$ 4.230.267,61) superam os TEDs em R$ 673.021,32. A diferença é coberta pela conta garantida (R23), e a causa é o pagamento antes da liquidação, a critério de quem paga (R25). Falta a regra de liquidação da Orbe para separar o que foi antecipado.
- **Causa raiz (R25): o caixa depende de uma decisão individual sem regra nem limite.** A Tarvo financia lojistas com a conta garantida sem política escrita, sem limite e sem registro de quem foi antecipado. O caso mais exposto é a Atlas: R$ 249.301,77 pagos em PIX em setembro, sem contrato (R3), depois de antecipar 1,8× o que vendeu no mês. Junto com a planilha de taxas incompleta (seção 3.1) e a condição da Casa do Estudante fora da planilha (R24), é o padrão de "regra que só uma pessoa sabe" que o financeiro descreveu.

---

## 5. Decisões de arquitetura

- **Dados como vêm**: nada é corrigido na origem. Limpeza só em colunas derivadas.
- **Sem banco transacional**: processamento em lote. Atomicidade por publicação em `saida/` só depois das validações. Ver [notebook, seção 2](exploracao_inicial.ipynb).
- **IA só onde há ambiguidade**: classificação de lançamentos sem padrão claro e sugestão de lojista por nome (sempre com confiança baixa e revisão humana). Números vêm sempre do código, com rastro.
- **Mapeamentos e retenções por configuração**: o de-para de EC e as retenções (Atlas) ficam em `config/mapeamento_ec.csv`, e as condições comerciais fora da planilha (Casa do Estudante) em `config/condicoes_especiais.csv`. Nada disso fica no código, para rodar em outubro sem mexer em `src/`.
- **Código particionado por domínio**: `src/<dominio>/`, com camadas leves dentro de cada um. O checkout está em `src/checkouts/` (leitura → regras → comissão → saída) e lê só `data/` e `config/`. A ingestão (`src/ingestao.py`) fica como está.
- **Testes durante o desenvolvimento**: `python -m unittest discover -s tests -t .` (só biblioteca padrão, sem dependência nova, R12). Os testes do checkout cobrem as regras pela interface pública e garantem determinismo: a mesma entrada em qualquer ordem dá o mesmo resultado, e duas execuções geram arquivos idênticos byte a byte.
- **Versionamento**: um commit por versão, pela skill `commit-versao`.
