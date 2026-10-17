# PLANO: divisão de tarefas

Branches: `checkout` (Marcelo), `remessa` (Gabriel), `bancos` (Pedro). Cada um commita só na sua branch. O merge em `main` acontece nos checkpoints (11h, 15h30, 17h30), feito pelo Pedro como integrador.

## Contrato comum (Pedro entrega primeiro, até ~9h45)
Marcelo e Gabriel dependem disto para gerar saídas compatíveis:
- Estrutura do repositório (`src/`, `dados/`, `saida/`, `config/`, `tests/`) e a CLI `--mes --entrada --saida`.
- O esquema dos 6 CSVs e a regra do `id_saida`.
- O formato do rastro: cada módulo devolve linhas `(id_saida, arquivo_origem, ref_origem, valor)`.
- O validador `soma(rastro) == valor reportado`.

## Pedro: `bancos` (integração)
| Output | Arquivo | Caminho |
|---|---|---|
| Contrato e CLI | `src/`, `config/` | Esqueleto, utilitários de CNPJ, valor e data, validador de rastro |
| Lançamentos classificados | `lancamentos_classificados.csv` | Ler Aurora (`L<n>`) e Meridiano (`FITID`), classificar pelo plano de contas só nas contas que aceitam lançamento. Regra primeiro; IA só onde não houver regra, com `metodo` e `confianca` |
| Pendências | `pendencias.csv` | Consolidar as pendências dos três módulos, cada uma com motivo e quem decide |
| Notas a emitir | `notas_a_emitir.csv` | A partir das comissões de checkout e remessa já validadas. Depende da resposta do financeiro sobre tomador e regime |
| Rastro e testes | `rastro.csv`, `tests/` | Unir os rastros e rodar o validador de ponta a ponta |

## Gabriel: `remessa`
| Output | Arquivo | Caminho |
|---|---|---|
| Ingestão da Ponte | `src/` | Extrair o xlsx do .eml, ler as abas, converter data serial do Excel, normalizar CNPJ |
| Comissão por lojista | `comissoes_por_lojista.csv` (linha REMESSA) | Calcular conforme a regra confirmada pelo financeiro (50% do spread da Ponte ou spread contratado) |
| Divergências de spread | `divergencias_taxa.csv` (linha REMESSA) | Comparar o spread aplicado com a coluna "Spread remessa" da tabela de taxas |
| Anomalias da Ponte | `pendencias.csv` | `PC-0926-0162` duplicada, 4 spreads negativos, operações "C/ RESSALVA", "Taxa travada D-1" e "reprocessada" |
| Rastro | `rastro.csv` (remessa) | Cada comissão aponta para os `Nº Operação` que a compõem |

## Marcelo: `checkout`
| Output | Arquivo | Caminho |
|---|---|---|
| Ingestão da Orbe e das taxas | `src/` | Ler os dois arquivos, ligar por EC (nunca por nome), normalizar os formatos mistos da planilha |
| Comissão por lojista | `comissoes_por_lojista.csv` (linha CHECKOUT) | Vendas, estornos, antecipações e reversões, conforme a regra do financeiro. **Este é o mínimo da entrega** |
| Divergências de taxa | `divergencias_taxa.csv` (linha CHECKOUT) | Transação por transação: taxa contratada contra aplicada, com o valor em reais. Inclui a vigência da Bridge |
| Casos sem cadastro | `pendencias.csv` | Atlas, Horizonte Intercâmbio, Horizonte Viagens e Kiwi |
| Rastro | `rastro.csv` (checkout) | Cada comissão aponta para os `id_transacao` que a compõem |

## Dependências e prazos
- **Antes das 11h:** cada um com a ingestão da sua fonte funcionando, mais o checkpoint 1.
- **Regras de negócio:** ninguém calcula comissão antes da resposta do financeiro (comissão de checkout e de remessa, tratamento de estorno, vigência da Bridge). Até lá, só a ingestão.
- **Corte às 15h30:** se o mínimo (comissão de checkout) não estiver correto, todos ajudam o Marcelo.

## Em aberto
- Quem faz as notas a emitir: proposto o Pedro por ser o integrador; a confirmar com o time.
