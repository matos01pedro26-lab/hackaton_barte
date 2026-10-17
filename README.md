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
python -m src.fechar --mes 2026-09
```

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
- A taxa do Fluente (0,79% aplicado contra 0,89% contratado) está sinalizada para a Helena; nenhuma decisão foi tomada no lugar dela.

## Pendências

Todas estão em `saida/pendencias.csv` com `quem_decide`. Nenhuma linha fica sem decisor. As pendências de banco vêm de `config/pendencias_bancos.csv`.

## Estrutura

`input/` brutos · `data/` tabelas padronizadas · `config/` regras como dado · `src/` código · `tests/` testes · `PROMPTS/` histórico e `MOMENTOS.md` · `HIPOTESES.md` premissas e perguntas.
