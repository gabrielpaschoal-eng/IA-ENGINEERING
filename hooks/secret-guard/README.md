# secret-guard

Hook `PreToolUse` (matcher `Bash`) registrado em `.claude/settings.json`. Script `secret_guard.py` (stdlib only). Foca em `git add`/`git commit` — antes que o arquivo entre no histórico.

## Duas checagens, independentes

1. **Nome de arquivo** (`blockedFilenamePatterns` em `hooks/config/secret-guard.json`): `.env`/`.env.*` (com exceção pra `.env.example`/`.env.sample`/`.env.template` — prefixo `!` no JSON), `*.pem`, `*_rsa`, `id_rsa*`, `*.key`, `*.pfx`, `*.p12`, `*credentials*.json`, etc.
2. **Conteúdo** (`contentPatterns`, regex): chave AWS (`AKIA...`), bloco de chave privada (`-----BEGIN ... PRIVATE KEY-----`), padrão genérico `api_key/secret/token/password = "valor longo"`.

A mensagem de negação **nunca mostra o valor do secret encontrado** — só a regra/padrão que bateu.

## Como resolve o que checar

- `git add <arquivo>`: usa exatamente os pathspecs dados. `git add .`/`-A`/`--all` (ou nenhum pathspec): usa `git status --porcelain --untracked-files=all` do repo alvo pra saber o que seria staged.
- `git commit`: usa `git diff --cached --name-only` (o que já está staged). Se a flag `-a`/`--all` estiver presente, também inclui modificados-não-staged (`git diff --name-only`), já que `-a` auto-stageia eles no commit.
- Pra `add`, o conteúdo escaneado é o arquivo inteiro (até 200KB); pra `commit`, só as linhas **adicionadas** no diff staged (`git diff --cached -U0`) — não escaneia linha que já existia antes.
- Resolve repo/cwd do mesmo jeito que o `git-branch-guard` (`-C`/`--git-dir` da própria invocação, ou `cwd` da sessão vindo do payload do hook).

## Config

`hooks/config/secret-guard.json`: `blockedFilenamePatterns` (glob, prefixo `!` = exceção), `contentPatterns` (regex), `exemptRepos` (path absoluto do toplevel onde a guardrail desliga).

## Testes

```bash
python3 hooks/secret-guard/test_secret_guard.py -v
```
