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

---

# Momentos que importaram (Marcelo, linha de checkout)

Histórico completo das sessões do Claude Code, na ordem. Os três e-mails pessoais do time viraram `[e-mail pessoal removido]`; o resto está sem edição. Cópia das 17h07 de 17/10 (as sessões seguiram depois disso).

| Sessão | Arquivo | Modelo | O que foi feito |
|---|---|---|---|
| 1 | [`marcelo_1_contexto_sessao_claude_code.jsonl`](marcelo_1_contexto_sessao_claude_code.jsonl) | Claude Opus 5.5 (`claude-opus-5-5`) | Exploração dos dados, regras com o financeiro e o primeiro cálculo do checkout |
| 2 | [`marcelo_2_checkout_e_classificacao_sessao_claude_code.jsonl`](marcelo_2_checkout_e_classificacao_sessao_claude_code.jsonl) | Claude Opus 5.5 (`claude-opus-5-5`) | Divergências e pendências do checkout, conferências independentes e a tentativa do JEV |
| 3 | [`marcelo_3_fechamento_e_tela_sessao_claude_code.jsonl`](marcelo_3_fechamento_e_tela_sessao_claude_code.jsonl) | Claude Opus 5.5 (`claude-opus-5-5`) | Estudo das saídas, diagrama do fluxo, histórico dos meses fechados e correções da tela e do comando |

Nenhuma sessão chamou subagentes. As personas de revisão do time (Bia, Caio e Helena) estão em `.claude/agents/`, e as skills (`commit-versao`, `consulta`) em `.claude/skills/`.

## 1. A IA quebrou o fechamento ao testar o JEV (erro da IA)

Pedi para trocar as regras de classificação dos extratos por um modelo de decisão barato, o JEV da TypeSafe, com cache e roteamento pela confiança. A IA primeiro disse que não conhecia o modelo e só achou a documentação quando pedi a pesquisa na web. Na implementação, ela acrescentou os limiares de confiança em `config/parametros.csv` com `;` dentro do texto do motivo e rodou só os testes do módulo novo. A ingestão passou a recusar o arquivo, e o fechamento parou na tela ("linha com campos a mais"). A IA corrigiu quando rodou a suíte inteira, mas eu desfiz tudo e pedi um plano filtro a filtro antes de implementar de novo.

## 2. Perguntei se o checkout não deveria ter cruzado com o extrato do banco

A IA não mudou o cálculo só porque perguntei: testou nos dados primeiro. Mostrou que os PIX de repasse não batem com o líquido da Orbe em nenhuma janela (Lisboa recebeu R$ 17.642, contra R$ 161.700 de líquido) e que a regra R24 da Helena dispensa a conciliação parcela a parcela. A comissão continuou vindo do relatório da Orbe pela taxa contratada. Mais tarde pedi uma coluna de "comissão verdadeira" pelo extrato, e a IA mostrou que ela não é calculável com os dados antes de mexer no arquivo.

## 3. Conferência independente da ingestão

Pedi para conferir se as tabelas de `data/` batiam com os arquivos brutos e com o que o checkout usa. A IA escreveu um script de conferência separado da ingestão do Pedro: os dados batiam, mas ela achou uma dependência escondida. A tarifa zerada da Casa do Estudante só vinha de `config/condicoes_especiais.csv`, e sem esse arquivo a comissão total iria para R$ 222.437,15. Decidi não mexer no código perto da entrega e registrar no `HIPOTESES.md` como ponto em aberto (a condição em dois arquivos de config).

## 4. Saídas só com as colunas do edital

No `divergencias_taxa.csv`, a IA propôs colunas a mais (data, tipo, faixa e origem da taxa) para facilitar a conferência. Proibi: as saídas têm exatamente as colunas do edital. A IA deixou essas informações só em memória, para os testes, e a integração com setembro passou a conferir as 7 colunas e os números-alvo do notebook do Pedro (92 divergências, R$ 1.576,23).
