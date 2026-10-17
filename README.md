# Fechamento Tarvo, setembro/2026

Pipeline que lê o data pack (Orbe, Ponte, extratos Aurora e Meridiano, planilha de taxas, plano de contas) e gera os seis arquivos do edital em `saida/`.

## Como rodar

Python 3.11 ou mais novo. **Não há nada para instalar** (só a biblioteca padrão) e **não há chave de API para configurar**: nenhuma etapa chama IA em execução. A classificação dos extratos é 100% por regra, e as regras vêm do financeiro (`config/` e `HIPOTESES.md`).

```
git clone https://github.com/matos01pedro26-lab/hackaton_barte
cd hackaton_barte
```

### Opção 1: um comando

```
python -m src.fechar --mes 2026-09 --sem-arquivar
```

Setembro **já está fechado e arquivado** em `fechamentos/2026-09/`, e mês fechado não reabre. Por isso a rodada de reprodução usa `--sem-arquivar`: ela refaz o cálculo e grava os seis arquivos em `saida/` sem mexer no arquivo do mês. Sem essa opção, o comando para com o aviso "2026-09 já está fechado" (veja "Fechar um mês novo", abaixo).

Lê os arquivos do mês em `input/`, roda ingestão, checkout, remessa, consolidação e validador, grava os seis arquivos em `saida/` e imprime o resumo (comissão, notas, divergências, pendências). O mês é sempre informado, e nada no código está fixo em setembro. Para outro mês, ponha os arquivos novos (mesmo formato) numa pasta e aponte para ela: `python -m src.fechar --mes 2026-10 --entrada <pasta>`.

### Opção 2: tela

```
python -m src.app
```

Abre uma página no navegador (`http://127.0.0.1:8765`). Ela roda **no computador de quem executa**: `127.0.0.1` significa "esta máquina", e o servidor é o próprio comando acima, sem internet nem instalação. Na página: arraste os arquivos do mês (ou use os do case), clique em **Fechar o mês**, veja o dashboard (comissão por lojista, divergências, pendências, notas e extratos), clique em qualquer número para ver as linhas de origem e baixe os seis CSVs (ou o zip). Cada rodada fica em `execucoes/` e não altera o `saida/` entregue.

### Etapa a etapa (o que `src.fechar` faz por baixo)

```
python -m src.ingestao  --mes 2026-09 --entrada input --saida data
python -m src.checkouts --mes 2026-09 --entrada data --config config --saida saida/checkouts
python -m src.remessa   --mes 2026-09 --dados data --saida saida/parcial
python -m src.consolidar --mes 2026-09        # grava os seis arquivos na raiz de saida/
python -m src.validador                       # confere formato, rastro por id_saida, notas, contas e saldo
python -m unittest discover -s tests -t .     # testes
```

`consolidar` só grava se o validador passar. `saida/checkouts/` e `saida/parcial/` são saídas intermediárias dos módulos e são mantidas.

## Fechar um mês novo (outubro em diante)

```
python -m src.fechar --mes 2026-10 --entrada <pasta com os arquivos de outubro>
```

1. Ponha os arquivos do mês numa pasta, com os mesmos prefixos (`01_orbe…`, `02_tabela_taxas…`, `03_email_ponte…`, `04_plano_de_contas…`, `05a_…aurora…`, `05b_…meridiano…`). Os ajustes tardios da Orbe (`06_orbe_…`) são opcionais.
2. Rode o comando. Ele para com aviso, sem gravar nada, se faltar arquivo, se as datas não forem do mês pedido, se uma transação da Orbe já tiver sido faturada num mês fechado ou se o validador não fechar.
3. Se tudo passar, o mês é **arquivado em `fechamentos/AAAA-MM/`** e não reabre (P20). O mês fecha quando a Helena aprova (RC-12): enquanto ela revisa, rode com `--sem-arquivar` e arquive só depois da aprovação. Commite essa pasta: é o histórico que o mês seguinte consulta.
4. O resumo lista as **pendências herdadas** dos meses anteriores. Quando quem decide resolver uma delas, registre uma linha em `config/pendencias_resolvidas.csv` (`id_saida;resolvido_em;decisao;quem_decidiu`), e ela deixa de ser herdada.

| Pasta | O que guarda |
|---|---|
| `fechamentos/AAAA-MM/manifesto.json` | Quando fechou, commit, arquivos de entrada com sha256 e totais |
| `fechamentos/AAAA-MM/saida/` | Os seis arquivos entregues naquele mês |
| `fechamentos/AAAA-MM/data/` | `fato_orbe`, `fato_ponte`, `fato_banco`, `dim_ec`, `controle_ingestao` |
| `fechamentos/AAAA-MM/pendencias_abertas.csv` | Pendências do mês e herdadas ainda abertas, com o mês de origem |

Para uma rodada de teste que não arquiva: `--sem-arquivar`. Para corrigir um mês fechado errado: `--refazer` (o anterior fica guardado em `anterior_<hora>/`).

**Próximos passos** (planejados, ainda não feitos):
- reconhecer cada arquivo pelo conteúdo, e não pelo prefixo do nome;
- aceitar arquivo tardio de mês fechado no mês aberto;
- faturar as linhas retidas da Atlas quando o comercial confirmar a taxa;
- dar baixa automática nas pendências herdadas: transferência em trânsito, PIX sem operação e ajuste da Ponte;
- levar as regras de classificação e os nomes de coluna esperados para `config/`.

## Saídas (`saida/`)

`comissoes_por_lojista.csv`, `divergencias_taxa.csv`, `notas_a_emitir.csv`, `lancamentos_classificados.csv`, `pendencias.csv`, `rastro.csv`. Separador `;`, decimal com ponto e 2 casas, datas ISO, CNPJ com 14 dígitos. Em `rastro.csv`, a soma por `id_saida` é igual ao valor reportado.

## Classificação dos extratos

Regra primeiro (`src/classificacao.py`, `REGRAS`); IA só onde não há regra, com confiança limitada e só em conta que aceita lançamento. Sem regra e sem sugestão válida: `metodo = HUMANO`, sem conta, e pendência. Todas as contas gravadas aceitam lançamento no plano. Em setembro, os lançamentos saem por regra; a IA não foi acionada.

## Limitações e premissas

- Regras vêm do edital e das respostas do time financeiro no Slack. `HIPOTESES.md` e `PLANO.md` são nossos; o que só consta lá é premissa, não regra confirmada.
- Premissas marcadas na coluna `premissa` dos lançamentos: Google Workspace (L48) em 4.2.04 e devolução de PIX (L65) em 2.1.01.001.
- O extrato do Meridiano não traz saldo inicial, então a soma dele não é conferida contra o saldo; só a do Aurora é.
- `RAZÃO SOCIAL A CONFERIR`: as notas usam o nome do cadastro; a razão social não foi confirmada.
- Não há nota para lojista com comissão zero ou negativa (Casa e Atlas): vira pendência.
- Prazo de contestação da Ponte: a data nas pendências é calculada do e-mail (5 dias úteis, sem feriados) e **está a confirmar com a Helena**.
- A taxa do Fluente (Pix a 0,79%, contra 0,89% dos demais lojistas) foi **confirmada pela Helena como condição negociada**: não é erro da planilha e não gera pendência.
- Se faltar uma das seis fontes, o fechamento **não roda parcial**: para, sem gravar nada, e diz o que falta. A Helena prefere fechar o que não depende da fonte que faltou; ainda não fazemos isso.
- As pendências de banco escritas à mão (`config/pendencias_bancos.csv`) valem só no mês da coluna `mes`. Em outro mês, o fechamento só aponta lançamentos sem regra; as demais pendências de banco do mês novo precisam ser escritas.
- O que o mês fechado deixa em aberto (por exemplo a Atlas, retida até o comercial confirmar a taxa) é **herdado como pendência** pelo mês seguinte, mas o faturamento retroativo continua dependendo da decisão do comercial.

## Pendências

Todas estão em `saida/pendencias.csv` com `quem_decide`. Nenhuma linha fica sem decisor. As pendências de banco vêm de `config/pendencias_bancos.csv`.

## Estrutura

`input/` brutos · `data/` tabelas padronizadas · `config/` regras como dado · `src/` código · `tests/` testes · `PROMPTS/` histórico e `MOMENTOS.md` · `HIPOTESES.md` premissas e perguntas.
