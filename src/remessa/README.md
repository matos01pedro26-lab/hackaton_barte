# Módulo de remessa

Fecha a linha de **remessa** (Ponte Câmbio): comissão por lojista, divergências de spread, pendências, nota da Ponte e rastro.

## Como rodar

Da raiz do repositório, depois da ingestão (`python -m src.ingestao --mes 2026-09 --entrada . --saida data`):

```
python -m src.remessa --mes 2026-09 --dados data --saida saida/parcial
python -m unittest discover -s tests -t .
```

Só biblioteca padrão do Python (3.10 ou mais). Para outro mês, troque `--mes` e use os arquivos novos no mesmo formato: nada no código muda.

## O que lê e o que grava

Lê só as tabelas prontas da ingestão: `data/fato_ponte.csv`, `data/dim_contrato_taxa.csv`, `data/dim_lojista.csv`.
Grava seis arquivos em `saida/parcial/`; quem os junta aos CSVs finais do case (com o checkout) é a integração.

| Arquivo | Conteúdo | `id_saida` |
|---|---|---|
| `remessa_comissoes.csv` | comissão por lojista (`linha_negocio = REMESSA`) | `REM-AAAA-MM-<cnpj>` |
| `remessa_divergencias.csv` | spread aplicado contra o contratado, valor cheio | `DIV-REM-AAAA-MM-<Nº operação>` |
| `remessa_pendencias.csv` | o que exige uma pessoa, com motivo e quem decide | `PEN-REM-AAAA-MM-<TIPO>-<ref>` |
| `remessa_notas.csv` | nota única da Ponte (formato de `notas_a_emitir`) | `NF-REM-AAAA-MM-<cnpj da Ponte>` |
| `remessa_rastro.csv` | uma linha por operação que compõe cada número | o do número que sustenta |
| `remessa_resumo.csv` | contagens e totais do mês | |

Os ids são chaves naturais (CNPJ, Nº da operação), estáveis de um mês para o outro. O rastro é validado a cada execução:
a soma por `id_saida` tem que bater com o número reportado, ao centavo, senão o programa para com erro.

## Regras (todas confirmadas pelo financeiro; ver `HIPOTESES.md`)

- **Comissão** = 50% do `Spread R$` realizado da Ponte, por operação, arredondada ao centavo (meio centavo para longe do zero) e somada por lojista. Vale a **data de contratação**.
- **Fora da comissão e da nota**: operação repetida (conta uma vez) e spread negativo (a trava passou de 2 horas). "Aprovado c/ ressalva" não muda nada.
- **Ajuste da Ponte** (linha com observação `AJUSTE REF PC-…`): entra no mês em que aparece e abate a participação; o rastro guarda a operação original (`ref_original`).
- **Divergência** = `Spread R$` − spread contratado × Valor ME × PTAX, valor cheio. Spread em branco ou "padrão" vale 1,5%. Só é reportada se passar das duas tolerâncias: `tolerancia_spread_pp` (0,005 p.p., em `config/parametros.csv`, com o estudo em `notebooks/remessa_tolerancia.ipynb`) e `tolerancia_brl` (0).
- **Spread negativo** entra como divergência e vira pendência com **dois valores**: o do relatório (`SPREAD_NEGATIVO`) e a diferença até o contrato (`CONTESTACAO_ATE_CONTRATO`).
- **Nota**: uma só, tomadora Ponte Câmbio, pelo total. Total zerado ou negativo não emite e vira pendência.
- **CNPJ sem linha vigente na tabela de taxas**: calcula a participação mesmo assim (a Ponte paga) e abre pendência de cadastro para o comercial.

## Configuração

- `config/parametros.csv`: spread padrão e tolerância do spread (compartilhados com a ingestão, com fonte e quem aprovou).
- `config/remessa.json`: participação da Tarvo, tolerância em reais, padrão do ajuste, tomador da nota e quem decide cada pendência.

## Limitações conhecidas

- A tolerância vem de um mês de dados (14 lojistas, uma divergência real). Rever com outubro.
- O ajuste da Ponte foi testado com uma linha sintética: setembro não tem nenhum.
- Operação fora do mês de contratação vira pendência (`FORA_COMPETENCIA`) e não entra na comissão.
- A conciliação com o banco (TED à Ponte, Pix dos lojistas) não é feita aqui.
