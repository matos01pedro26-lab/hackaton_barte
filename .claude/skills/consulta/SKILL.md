---
name: consulta
description: Consulta os três agentes do financeiro (Bia, Caio e Helena) para revisarem o trabalho feito no projeto e dar, cada um, seu parecer sobre o que pode estar errado e como corrigiriam. Use quando o usuário digitar /consulta ou pedir uma revisão/parecer do time.
---

# consulta

Reúne o parecer dos três revisores. Argumento opcional: foco da revisão (ex.: "notas", "remessa", "setembro"); sem argumento, revise o trabalho como um todo.

## Passos
1. Rode `git status --short` e `git log --oneline -5` para saber o que mudou; resuma em 2–3 linhas para dar contexto aos agentes.
2. Dispare os **três agentes em paralelo, numa única mensagem** (tool Agent), cada um com `subagent_type` próprio, passando o contexto do passo 1 e o foco pedido:
   - `bia-checkout`: checkout, taxas, ECs, divergências;
   - `caio-bancos-remessa`: Ponte, remessa, extratos, classificação;
   - `helena-financeiro`: regras confirmadas, notas, exceções, aprovação.

   Peça a cada um o parecer no formato do seu próprio prompt. Eles são somente leitura.
3. Quando voltarem, apresente em português:
   - um bloco por pessoa (veredito + pontos + correção), fiel ao que cada uma disse;
   - **Pontos em comum**, **Discordâncias** entre eles e uma **lista priorizada de correções** (impacto em R$ primeiro).
4. Não aplique correções sem o usuário pedir. Não invente números que os agentes não tenham verificado.
