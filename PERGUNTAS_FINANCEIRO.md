# Perguntas para o financeiro: rodada 3 (T-800, 17/10)

Rodada nova, para fechar o que ainda é PREMISSA. Cada item diz a **hipótese** que o fechamento já usa (quando é cálculo, a hipótese vale até a resposta) e a **pergunta** objetiva. Quem responde está entre parênteses.

Respostas anteriores estão em `duvidas_financeiro.csv` (#39 e #40). Para virar CONFIRMADO em `config/registro_decisoes.csv`, a resposta precisa entrar nesse CSV, sem edição, com o número da linha.

---

## Para a Helena (financeiro)

**7. Fluente, Pix a 0,79%.**
- Hipótese (cálculo): comissão do Pix da Fluente a 0,79% sobre a base de R$ 9.136,16, o que dá R$ 72,18. A nota de R$ 7.316,07 já usa 0,79%. A diferença para 0,89% seria R$ 9,16.
- Pergunta: 0,79% é a condição contratada e vigente? Confirma por escrito?
- Se confirmar: a pendência `TAXA_A_CONFIRMAR` (R$ 9,16) fecha.

**8. Juros da conta garantida.**
- Hipótese: nenhum juro lançado em setembro (extrato sem juros, IOF ou tarifa dessa conta). A referência é o menor saldo do mês, −R$ 2.289.532,94, marcado "não somar".
- Pergunta: os juros da conta garantida entram no extrato de outubro? Em qual conta devemos lançar (4.3.02 juros e multas, ou outra)?
- Se confirmar: a pendência `CONTA_GARANTIDA_SEM_ENCARGOS` fecha com o lançamento correto em outubro.

**9. Razão social das notas.**
- Hipótese: o tomador é o nome da planilha de taxas com o CNPJ, e a razão social oficial só entra na emissão.
- Pergunta: a Bia confere a razão social antes de emitir cada nota? A conferência é feita para as 20 notas de checkout e a da Ponte? Por escrito, quem confirma e até quando?
- Se confirmar: a pendência `RAZAO_SOCIAL_NOTAS` (R$ 203.740,84) fecha.

**10. Prazo da contestação à Ponte.**
- Hipótese (cálculo): o e-mail de 02/10 dá 5 dias úteis, o que leva a **09/10/2026**, sem feriados. Esse prazo já venceu em 17/10.
- Pergunta: qual é o prazo formal? A Ponte aceita contestação fora do prazo? Essa resposta precisa vir **da Ponte, por escrito**; a Helena pode confirmar qual canal usar.
- Enquanto não houver resposta, a contestação de R$ 1.418,88 (Mundo Aberto), dos 4 spreads negativos (R$ 3.565,98 até o contrato) e da duplicata (R$ 410,94) não sai.

**11. Duplicata na contestação.**
- Hipótese: a duplicata PC-0926-0162 entra na contestação, pelo valor de R$ 410,94 (parte da Tarvo). Os R$ 821,88 do relatório não são cobrados duas vezes.
- Pergunta: confirma que a duplicata entra na contestação à Ponte? Pelo valor de R$ 410,94 ou pelo total de R$ 821,88?

**12. Valor da Mundo Aberto.**
- Hipótese: R$ 1.418,88 (Spread R$ realizado, valor cheio pago pelo lojista).
- Pergunta: confirma o valor a pedir à Ponte? (A diferença para R$ 1.418,85 pelo spread % é de centavos.)

**13. Casa do Estudante a partir de 2027.**
- Hipótese (calendário): a isenção termina em 31/12/2026. A partir de 01/01/2027 a taxa volta à planilha, sem condição.
- Pergunta: confirma? Se o comercial renovar, quem registra a nova condição, e em que data?

---

## Para o Diego (comercial)

**14. Atlas (EC 1076801732).**
- Hipótese: a Atlas segue retida, sem comissão, sem nota. Pendência `EC_RETIDO` (R$ 7.876,05 de taxa estimada da Orbe) com o Diego, prazo fechamento de outubro.
- Pergunta: qual é a taxa contratada da Atlas e a data em que ela vale? Se o contrato não estiver assinado, há previsão de assinatura?

---

## Para a Bia (checkout)

**15. Cadastro dos ECs e da condição da Casa.**
- Hipótese: os ECs 1043300981 (Novo Horizonte), 1043396662 (Horizonte Viagens) e 1038867654 (Kiwi) e a condição da Casa ainda não estão registrados na planilha de taxas. São as 4 pendências `CADASTRO_EC` e `CADASTRO_CONDICAO`, com a Bia.
- Pergunta: já registrou? Se não, em qual data? Ao registrar, avisa a Helena para ela rodar de novo.

---

## Para o Caio (bancos)

**16. PIX de R$ 7.350,00 sem identificação (16/09, CNPJ 38.686.002/0001-80, linha L50).**
- Hipótese: o pagador não foi identificado. O lançamento está em `1.1.09.002` (créditos não identificados), com confiança 0,70 e pendência aberta.
- Pergunta: achou o pagador? Se achou, qual é, e em qual conta devemos reclassificar?

---

## Feito, sem pergunta

- **Sessão do checkout (Ryaj / Marcelo):** já está em `PROMPTS/` (três arquivos `marcelo_*`), como o time disse no item 4.
- **Mês sintético (outubro):** o teste está em `tests/test_mes_sintetico.py`. Resultado: fecha, com checkout de R$ 203.740,84 (a Casa sobe R$ 5,50) e divergências iguais às de setembro. Bank pendências de setembro não valem em outubro, e isso é o comportamento esperado.
