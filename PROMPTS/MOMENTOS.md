# Momentos que importaram (Gabriel, linha de remessa, integração e pitch)

Histórico completo da sessão: [`gabriel_remessa_sessao_claude_code.jsonl`](gabriel_remessa_sessao_claude_code.jsonl). O arquivo tem **duas** edições, e só elas: o e-mail pessoal foi removido, e as **imagens (capturas de tela) foram omitidas e trocadas por um marcador**, só para o arquivo ficar dentro do limite de tamanho do repositório (45 MB com as imagens, 31 MB sem). O texto da conversa, os pedidos, as respostas da IA e as saídas dos comandos estão sem edição. A cópia foi feita às 16h42 de 17/10, e a sessão seguiu depois disso.

## 1. A IA propôs uma regra que a Helena depois desmentiu (erro da IA)

Pedi para registrar como tratar os ajustes que a Ponte manda depois de uma contestação. A IA propôs a premissa P9: linha do relatório que não é operação de câmbio vira pendência, fora da comissão e da nota. Nenhum dado de setembro mostrava como o ajuste aparece, e aprovei por ser a opção conservadora. Mais tarde a Helena respondeu no canal que o ajuste vem como linha nova, `AJUSTE REF PC-…`, e que abate a nossa participação do mês dentro da nota única. A premissa estava errada: mandei implementar a regra confirmada, a P9 virou "superada" e há um teste de ponta a ponta com uma linha sintética de ajuste.

## 2. A tolerância saiu de um estudo, não de um palpite

Pedi que a tolerância da divergência de remessa começasse em zero e fosse decidida olhando os dados por lojista: se um lojista erra sempre o mesmo centavo, corrige-se só ele; se o erro é aleatório, aceita-se ±0,01. A IA fez a análise exploratória e mostrou que nenhum lojista tem viés, que o ruído da Ponte fica em ±0,0016 p.p. e que a única divergência real, a Mundo Aberto, está em +0,30 p.p.; em reais a separação é ruim, porque o ruído cresce com o valor da operação. Adotei 0,005 p.p., e a decisão ficou em arquivo de configuração, com o motivo escrito.

## 3. Revisão crítica do trabalho do Pedro, com recálculo independente

Pedi uma análise crítica da parte do Pedro. A IA recalculou a comissão de checkout do zero, direto dos arquivos brutos e sem usar a ingestão dele, e bateu com os números dele. Mas achou dois problemas de interpretação: a Casa do Estudante estava dentro das divergências de contrato, contra a resposta da Helena ("a devolução da Casa fica separada das divergências"), e o arquivo de perguntas repetia perguntas já respondidas no canal. O Pedro autorizou as correções, e fiz só as mudanças mínimas.

## 4. Testar como a banca testaria, e achar o que o nosso próprio teste não via

Pedi para saber se a solução rodava em outros meses. A IA fabricou um "outubro de teste" deslocando as datas de setembro e rodou o comando de verdade, e isso expôs quatro defeitos: o checkout calculava R$ 207 mil e chamava de outubro, sem avisar ninguém; as pendências de banco estavam presas a IDs de setembro e derrubavam o fechamento; o prazo da Ponte tinha a data de setembro fixa; e uma pendência minha ("nota não emitida") não tinha rastro. Corrigimos os quatro, com testes. Depois, na `main`, a mesma prática de clonar limpo e rodar o README achou que a mudança de um colega (arquivar o mês fechado) fazia o comando do README falhar para a banca, e que o pitch tinha ficado desatualizado depois de a Helena confirmar a Fluente como condição negociada.

---

# Momentos que importaram (Pedro, bancos e integração)

Históricos completos: [`pedro_bancos_integracao_sessao_claude_code.jsonl`](pedro_bancos_integracao_sessao_claude_code.jsonl) (construção) e [`pedro_revisao_consulta_sessao_claude_code.jsonl`](pedro_revisao_consulta_sessao_claude_code.jsonl), com os subagentes revisores em [`pedro_revisao_consulta_subagentes/`](pedro_revisao_consulta_subagentes/). Só os e-mails pessoais foram removidos; o resto está sem edição.

## 1. A IA anunciou uma mudança de número que não existia (erro da IA)

Pedi para aplicar a resposta da Helena de que o Pix a 0,79% da Fluente é condição negociada, e a IA disse que a nota da Fluente cairia de R$ 7.316,07 para R$ 7.306,91. Antes de mexer no CSV, ela conferiu nos dados e viu que a nota já saía a 0,79% (a pendência de R$ 9,16 era só a diferença para 0,89%), então corrigiu o que tinha dito e eu aprovei só a mudança na pendência, sem alterar nenhum valor.

## 2. Tratamos resposta colada no chat como regra oficial (a IA me levou para o lugar errado)

Pedi para fechar as hipóteses e as regras de negócio com as respostas da Helena ao T-800, e a IA marcou como confirmadas respostas que estavam só no chat, fora do `duvidas_financeiro.csv`. A revisão com os agentes Bia, Caio e Helena apontou o problema; reabrimos as pendências da Fluente, dos juros da conta garantida e da razão social, e criei `config/registro_decisoes.csv`, onde só é CONFIRMADO o que tem resposta escrita no CSV.

## 3. Desconfiei de 184 lançamentos todos "por regra"

Estranhei que nenhum lançamento saía por IA ou para humano e pedi a origem das 26 regras de classificação. A IA mostrou que o caminho de IA nunca tinha sido ligado e que várias regras eram inferência dela, sem resposta do financeiro; pedi para separar o que era do financeiro, do time e da IA, e as suposições viraram as perguntas da rodada T-800.
>>>>>>> Stashed changes
