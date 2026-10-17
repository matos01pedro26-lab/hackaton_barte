# Roteiro de fala · pitch T-800 (15 min + 5 de perguntas)

Público: o time financeiro e o CFO da Tarvo. Linguagem de dinheiro e de decisão, sem jargão técnico.
Estrutura: **resposta primeiro**, depois **STAR** (Situação, Tarefa, Ação, Resultado) seguindo a linha de um achado de auditoria
(critério, condição, causa, efeito, recomendação).

| STAR | Achado de auditoria | Slides |
|---|---|---|
| S · Situação | condição (o que está quebrado) e critério (o que deveria acontecer), mais a causa raiz | 3, 4 |
| T · Tarefa | escopo e objetivo | 5 |
| A · Ação | procedimentos: o que fizemos | 6, 7, 8, 9 |
| R · Resultado | efeito quantificado e recomendações | 10, 11, 12, 13, 14 |

## Divisão sugerida (a decisão é de vocês)

| Quem | Slides | Tempo |
|---|---|---|
| Gabriel | 1, 2 (abertura e a resposta em uma página) | 2:00 |
| Marcelo | 3, 4, 5 (Situação e Tarefa: o checkout é a história do problema) | 3:00 |
| Pedro | 6, 7, 8 (Ação: como a solução trabalha, perguntar antes, onde a IA atua) | 3:30 |
| Gabriel | 9 (**demonstração ao vivo na tela**: `?auto=exemplo`, clicar em um número) | 2:00 |
| Gabriel | 10, 11 (resultado e dinheiro em jogo) | 1:30 |
| Pedro | 12, 13 (pendências e onde falha) | 1:30 |
| Gabriel | 14, 15 (recomendações e encerramento) | 1:30 |

## O que dizer, slide a slide

1. **Capa.** “Entregamos o fechamento de setembro da Tarvo, com rastro de cada número até a linha de origem.”
2. **A resposta primeiro.** “Setembro está fechado: R$ 243 mil de comissão, 21 notas. Faltam 28 decisões que só uma pessoa pode tomar, e cada uma tem dono. R$ 15,4 mil são devolução ao lojista; R$ 6,5 mil são contestações com a Orbe e a Ponte.”
3. **Situação.** “Oito dias úteis, três pessoas, seis fontes. E a regra mora na cabeça da Helena: se ela sai de férias, o mês não fecha.”
4. **Critério e causa.** “As regras existem, mas não estão escritas em lugar nenhum. Automatizar do jeito que está só faria o erro rodar mais rápido; primeiro tornamos as regras explícitas.”
5. **Tarefa.** “Seis entregas, uma regra central: todo número aponta para a origem. E uma condição nossa: não assumir regra de negócio.”
6. **Ação, o fluxo.** “Os arquivos entram como vêm. As regras ficam em arquivos de configuração, com quem aprovou. No fim, um validador confere que a soma do rastro bate; se não bate, o programa para.”
7. **Perguntar antes de assumir.** Contar o caso do ajuste da Ponte: “nós assumimos que viraria pendência; a Helena disse que não; mudamos o código.” E o da tolerância de centavos: estudo, não palpite.
8. **IA.** “A IA nos ajudou a construir e a revisar, e errou uma vez. Mas nenhum número do fechamento vem dela: 184 de 184 lançamentos saem por regra. É dinheiro de terceiros: precisa ser auditável.”
9. **Outubro (demonstração).** Abrir a tela, usar os arquivos do case, clicar numa comissão e mostrar as linhas de origem somando. “Se o mês estiver errado, a solução recusa.”
10. **Seis saídas.** Passar rápido; destacar “validador: tudo fecha” e o R$ 5,50 de diferença (a Casa não emite nota).
11. **Dinheiro em jogo.** O slide mais importante para o CFO. Ler os seis cartões, nesta ordem: devolver, contestar Orbe, contestar Ponte, receita que sairia a maior, Atlas, banco.
12. **Pendências.** “Aqui a solução para e pergunta. O Pix da Fluente a 0,79% é um exemplo: o fechamento manual não percebe, nós sinalizamos.”
13. **Onde falha.** Ser direto: não fecha parcial, as pendências de banco de outubro não são automáticas, a Atlas não é levada ao mês seguinte.
14. **Recomendações.** Lado esquerdo: o que a Tarvo faz antes de outubro. Lado direito: o que faríamos com mais um mês.
15. **Fecho.** “O fechamento deixou de depender da cabeça de quem fecha.” Mostrar o repositório e o comando.

## Perguntas prováveis

- **“Por que não usaram IA no cálculo?”** Dinheiro de terceiros exige regra auditável e resultado repetível. A IA entraria só para sugerir, com revisão humana.
- **“E se a Helena não concordar com uma regra?”** Está em `config/` e no `HIPOTESES.md`, com quem aprovou; muda-se o arquivo, não o código.
- **“Funciona em outubro?”** Testamos com um outubro fabricado (datas de setembro deslocadas): fecha de ponta a ponta. Não testamos com dados reais de outubro, e as pendências de banco de setembro valem só em setembro.
- **“Por que R$ 15.396,77 e não R$ 15.397,42?”** O primeiro é o que a Orbe descontou de fato (a Helena disse que devolve o que saiu do bolso do lojista); o segundo é a fórmula de divergência, 65 centavos acima por causa do truncamento da Orbe.
- **“Qual a tolerância?”** 0,005 p.p. (3 vezes o ruído da Ponte, 60 vezes menor que a divergência real). É de um mês só: deve ser revista em outubro.

## Como o roteiro foi montado (fontes)

- STAR: situação e tarefa curtas, **ação é a parte mais longa**, resultado quantificado. Fontes:
  [Pomona College](https://cdo.pomona.edu/blog/2025/04/29/star-method-how-to-use-this-technique-to-ace-your-next-job-interview/),
  [CMU Tepper](https://www.cmu.edu/tepper/alumni/assets/docs/star-story.pdf). As fontes colocam o Resultado no fim; abrir pela
  conclusão é uma adaptação nossa para pitch.
- Achado de auditoria (critério, condição, causa, efeito, recomendação): causa não pode repetir a condição; efeito quantificado;
  recomendação específica e com prazo.
  [IIA, five attributes](https://internalauditor.theiia.org/en/articles/2023/february/the-five-attributes-approach/),
  [NIGC, elements of a finding](https://www.nigc.gov/images/uploads/Part_5_Elements_of_a_Finding_Participant_Guide.pdf),
  [CCCE model](https://open-exam-prep.com/study-guides/cia-part3/findings-root-cause-recommendations/core-elements-finding-ccce).
- CFO: falar em dinheiro, resumo curto com o detalhe como apoio, e tratar o que for estimativa como preliminar.
  [Salesforce](https://www.salesforce.com/blog/?p=70668), [ZoomInfo](https://pipeline.zoominfo.com/sales/selling-to-cfo),
  [Gong](https://www.gong.io/resources/guides/how-to-sell-to-cfo).
