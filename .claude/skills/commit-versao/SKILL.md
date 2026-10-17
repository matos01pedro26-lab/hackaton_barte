---
name: commit-versao
description: Faz commit da pasta atual com nome e descrição gerados a partir do que mudou desde a versão anterior. Antes de commitar, compara com o repositório remoto (origin); se houver divergência, lista quais são e pede validação do usuário em vez de seguir. Use quando o usuário pedir para versionar, commitar, salvar uma versão ou postar mudanças no GitHub. Com o argumento "push", também publica no origin.
---

# commit-versao

Versiona a pasta atual: um commit por versão, com nome e descrição que dizem **o que mudou em relação à versão anterior**. Antes de qualquer commit, confere se o repositório remoto (o "original") diverge do local. Se divergir, **para e pede validação**.

Argumentos: nenhum (só commita) ou `push` (commita e publica em `origin`).

## Passo 1 · Pré-checagem

```bash
git rev-parse --is-inside-work-tree     # tem que ser true
git remote get-url origin               # remoto configurado?
git branch --show-current               # branch atual
git config user.name && git config user.email   # identidade; se faltar, avise e pare
```

Se não for repositório git ou não houver `origin`, diga o que falta e pare. Não invente a URL do remoto.

## Passo 2 · Divergência com o original (obrigatório)

```bash
git fetch origin
```

Seja `B` a branch atual. Se `origin/B` **não existe** (remoto vazio), não há divergência: siga para o passo 3.

Se existe, calcule:

```bash
git rev-list --left-right --count HEAD...origin/B    # "à frente<TAB>atrás"
git log --oneline HEAD..origin/B                     # commits do remoto que não estão aqui
git diff --stat HEAD...origin/B                      # arquivos que o remoto mudou
```

Casos:

| Situação | O que fazer |
|---|---|
| Atrás = 0 (o remoto não tem nada novo) | Sem divergência. Siga. |
| Atrás > 0, ou o local ainda não tem commits e o remoto tem | **Divergência.** Pare e vá para "Relatório de divergência". |
| Histórias sem ancestral comum (`git merge-base HEAD origin/B` vazio) | **Divergência.** Mesmo tratamento. |

### Relatório de divergência

Mostre ao usuário, em linguagem direta:

1. Commits do remoto que o local não tem (hash curto, autor, data, assunto).
2. Arquivos que o remoto mudou (`git diff --name-status HEAD...origin/B`).
3. **Colisões**: arquivos que mudaram no remoto **e** que têm alteração local (interseção de `git diff --name-only HEAD...origin/B` com `git status --short`). Esses são os de maior risco.
4. O que aconteceria em cada saída possível.

Depois peça a validação com `AskUserQuestion`, com estas opções:

- **Integrar o remoto primeiro** (`git pull --rebase origin B`) e depois commitar. Recomendada quando não há colisões.
- **Commitar só local, sem publicar**: guarda a versão aqui e deixa a integração para depois.
- **Cancelar**: não muda nada.

Não commite, não faça pull e não publique até a resposta. **Nunca** use `--force` nem `--force-with-lease` por conta própria.

## Passo 3 · O que mudou desde a versão anterior

```bash
git status --short
git diff --stat HEAD            # se já existe commit
git diff HEAD -- <arquivo>      # leia as mudanças relevantes
```

Para entender a mudança, leia o diff, não adivinhe pelo nome do arquivo. Regras por tipo:

- **Notebooks `.ipynb`**: não leia o JSON. Resuma por conteúdo (títulos das seções em markdown, células de código adicionadas ou removidas).
- **Binários e dados** (`.xlsx`, `.zip`, `.docx`, `.csv` grandes): cite nome e tamanho; só diga o que mudou se você realmente comparou.
- **Arquivos novos**: diga para que servem, em uma frase.
- **Renomeados ou movidos**: diga de onde para onde.

## Passo 4 · Segurança antes de adicionar

Respeite o `.gitignore`. Antes de `git add`, procure segredos no que entraria:

```bash
git diff HEAD | grep -nE "(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC )?PRIVATE KEY|api[_-]?key\s*[:=])"
```

Também não adicione `.env*`, `*.pem`, `*.key`, `credentials*`. Se achar algo, **pare**, mostre o arquivo e a linha (sem repetir o segredo inteiro) e peça decisão. Liste ao usuário o que ficou de fora por causa do `.gitignore`, para ele saber.

## Passo 5 · Nome e descrição do commit

Número da versão: `N = (git rev-list --count HEAD, ou 0 se não há commits) + 1`.

**Assunto** (até 72 caracteres, português, verbo no imperativo):

```
vN: <o que mudou, em uma frase>
```

Exemplos: `v1: adiciona exploração inicial dos dados de setembro`, `v4: corrige vigência da Bridge no cálculo de divergências`.

O assunto descreve a **mudança em relação à versão N-1**, não o projeto inteiro. Se o commit mistura assuntos diferentes, nomeie pelo principal e liste o resto no corpo.

**Corpo** (linha em branco após o assunto):

```
Mudanças desde v(N-1):
- Adicionado: <arquivo ou pasta> — <para que serve>
- Alterado: <arquivo> — <o que mudou e por quê>
- Removido: <arquivo> — <motivo>

Fora do commit: <arquivos ignorados ou deixados de fora, se houver>
```

Termine com a linha de atribuição que o ambiente indicar para commits (`Co-Authored-By: ...`). Não invente o nome do modelo.

## Passo 6 · Commitar

```bash
git add -A
git commit -F <arquivo-temporário-com-a-mensagem>
```

Use arquivo temporário (ou here-string) para a mensagem, para não quebrar acentos e quebras de linha. Nunca use `--no-verify`. Se um hook falhar, corrija a causa e tente de novo (crie um commit novo, não use `--amend`).

## Passo 7 · Publicar (só com o argumento `push` ou se o usuário pedir)

```bash
git push -u origin B
```

Se o push for rejeitado, **não** force. Rode de novo a checagem do passo 2 e reporte.

## Passo 8 · Relatório final

Responda curto: hash e assunto do commit, quantos arquivos por tipo de mudança (adicionado, alterado, removido), o que ficou de fora, e se publicou ou não. Se houve divergência e o usuário escolheu um caminho, diga qual.

## O que não fazer

- Não commitar com divergência sem validação do usuário.
- Não reescrever histórico já publicado (`rebase`, `reset --hard`, `--amend`, force push) sem pedido explícito.
- Não descrever mudanças que você não viu no diff.
