# HIPOTESES

Premissas assumidas, perguntas feitas ao financeiro (Helena, Tarvo) e respostas recebidas, no canal #tarvo-financeiro.
Status de cada item: **confirmado** (a Helena respondeu) ou **premissa** (decisão nossa, ainda não confirmada).

## 1. Regras confirmadas pela Helena

### Todas as linhas
- **Arredondamento:** comum para o centavo, meio centavo para cima, com a mesma regra para negativos (-0,005 vira -0,01). Arredonda linha a linha e depois soma. A Orbe trunca; nós não.
- **Quem aprova regras:** taxa e condição comercial, o comercial aprova e a Helena registra. Regra de como fechar, a Helena aprova. Hoje, nas férias dela, ninguém fecha o mês.
- **Prazo de contestação à Ponte:** considerar dentro do prazo. Contestações ficam como pendência, com valor e operações.

### Checkout
- **Comissão:** é a taxa inteira (MDR e antecipação), sem desconto de custo da Orbe, calculada pela taxa **contratada**, não pelo `valor_taxa` da Orbe.
- **Estorno:** abate a comissão do mês do estorno, mesmo de venda de agosto. A taxa usada é a vigente na data da venda original. Agosto já está fechado e não é reaberto.
- **Antecipação:** entra na mesma nota. A reversão só anula a taxa da antecipação que ela reverte.
- **Divergência:** existe quando a taxa aplicada é diferente da contratada. Valor = `valor_bruto × (taxa_aplicada − taxa_contratada)`. Diferença de centavo por truncamento da Orbe não é divergência.
- **Divergência é devolução:** a Orbe já liquida o líquido ao lojista; quando cobra a mais, o lojista recebeu a menos e a Tarvo devolve.
- **Rota Global:** não houve mudança de contrato este ano. O +0,50 p.p. cobrado pela Orbe desde 12/09 é divergência.
- **Casa do Estudante:** tarifa zerada no checkout de setembro a dezembro (MDR e antecipação), por acordo do comercial. A Orbe cobrou sem saber; o cobrado é divergência e a Helena devolve ao lojista. A remessa segue normal.
- **ECs sem cadastro na planilha:** `1043300981` é Novo Horizonte Intercâmbio, `1043396662` é Horizonte Viagens e Turismo (empresas diferentes) e `1038867654` é Kiwi Experience. CNPJ e taxas estão nas linhas deles.
- **Atlas (`1076801732`):** começou a transacionar em 10/09 e não tem contrato assinado na planilha vigente. Não se fatura até o comercial confirmar. Quando confirmar, a taxa vale desde 10/09 e o fechamento seguinte puxa as linhas de setembro pendentes.
- **Vigência da Bridge (crédito à vista de 2,59% para 2,19% em 15/09):** vale a data do movimento na Orbe.
- **Estorno em setembro de venda de agosto da Casa do Estudante:** usa a taxa de agosto (a tarifa zerada só vale de setembro a dezembro).
- **Nota fiscal:** uma por lojista por mês, no valor da comissão do mês pela taxa contratada. Zero ou negativo não emite, e o negativo não passa para o mês seguinte automaticamente: vira pendência para a Helena. Discriminação: texto simples com o serviço e a competência.

### Remessa
- **Comissão:** 50% do "Spread R$" realizado da Ponte, calculado e arredondado por operação (50% de 262,01 = 131,01). Vale a data de contratação.
- **Spread padrão:** célula em branco ou "padrão" é 1,5% sobre a PTAX de referência.
- **Spread negativo:** não aceito (a trava vale 2 horas pelo contrato). Fica fora da comissão e da nota, e é contestado.
- **Spread negativo é divergência:** os 4 casos (PC-0926-0210, -0326, -0491 e -0545) entram em `divergencias_taxa.csv` com o valor cheio contra o contratado, além de ficarem fora da comissão e da nota e na lista de contestação.
- **Operação repetida:** o número da operação é único; conta uma vez e entra também na lista para a Ponte corrigir o relatório.
- **"Aprovado c/ ressalva":** o status de compliance não muda nada.
- **Divergência de spread:** o valor é o cheio (quem pagou a mais foi o lojista), não os 50% da Tarvo. A Mundo Aberto negociou 1,20% em julho; a diferença é divergência a contestar com a Ponte.
- **Nota da Ponte:** uma só, tomadora Ponte Câmbio, pelo total da participação do mês. Sai pelo **realizado**, incluindo o excesso da Mundo Aberto. Se a Ponte devolver, o ajuste sai no mês em que acontecer.
- **Ajustes da Ponte:** a Ponte responde por e-mail e envia o ajuste no relatório do mês seguinte, como crédito ou débito. A Helena registra no fechamento do mês em que ele aparece.
- **Conferir o TED de 06/10:** fica com a Helena. Não contar que a Ponte descontará algo do repasse.
- **CNPJ fora da planilha na Ponte:** calcular nossa metade do spread mesmo assim e abrir pendência de cadastro para o comercial. Não aconteceu em setembro.

### Bancos
- **`conta_codigo` é a contrapartida:** o que já estava registrado é baixado na conta onde estava e não vira receita ou despesa de novo.
- **Provisão:** folha e impostos são sempre provisionados; o pagamento do mês seguinte baixa a provisão. O repasse da Ponte de 04/09 (R$ 61.884,12) é o spread de agosto, já como comissão a receber.
- **Despesas diretas:** tarifas, aluguel, cloud, assinaturas e serviços entram direto na despesa do mês.
- **Orbe no Aurora:** a Orbe deposita tudo no Aurora. Os créditos da Orbe são classificados, sem conciliar parcela por parcela. O saldo negativo é a conta garantida.
- **Repasses a lojistas:** duas vezes ao mês, perto do dia 10 e do dia 24. A regra está no contrato de adesão de cada lojista (pasta do comercial).
- **Pix de R$ 7.350 sem identificação (16/09):** não é receita até alguém identificar.
- **Devolução Pix da Mundo Aberto (R$ 12.400):** é um repasse que voltou, com motivo desconhecido. As contas `2.1.01.001` e `2.1.01.002` são válidas; escolher uma, manter o critério e escrever o motivo.
- **Transferência de R$ 300.000 para o Meridiano (30/09):** saiu do Aurora em 30/09 e cai no Meridiano em 01/10.
- **Pix de R$ 18.240 da Ponte Aérea no Meridiano (17/09):** é dinheiro de uma remessa que sai em outubro.

## 2. Premissas nossas (não confirmadas)

### P1. Linhas de ajuste da Ponte viram pendência
No fechamento de outubro, qualquer linha do relatório da Ponte que não seja uma operação de câmbio normal (por exemplo, crédito ou débito de ajuste) não entra na comissão nem na nota. Vira pendência em `pendencias.csv`, com valor e motivo, para a Helena decidir.
**Por quê:** o formato do ajuste não está nos dados de setembro. Tratar uma linha desconhecida como operação normal poderia faturar um valor errado.

### P2. Fluente Idiomas: Pix a 0,79% é pendência
A planilha traz 0,79% de Pix, enquanto os demais lojistas têm 0,89%. A Orbe cobrou 0,79% nas 8 vendas de Pix da Fluente, então não há divergência entre a planilha e a Orbe. A suspeita é de erro de digitação na planilha.
**Decisão:** calculamos a comissão pela planilha como está (0,79%) e abrimos uma pendência com as 8 transações. Quem decide: comercial (aprova taxa), com a Helena registrando.
**Destaque no case:** é um erro que o fechamento manual não percebe.

### P3. Tolerância da divergência de remessa (a definir pelo time)
A Helena deixou o critério para nós, desde que escrito e com motivo. O spread aplicado oscila ±0,002 p.p. em torno do contratado. Valor a ser definido pelo grupo.

### P4. Contas do Pix sem identificação, da devolução Pix e da transferência de R$ 300.000 (a definir pelo Pedro)
A Helena deixou a escolha para nós. Escolha, critério e motivo serão registrados aqui pelo Pedro.
