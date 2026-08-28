# git-branch-guard

Hook `PreToolUse` (matcher `Bash`) registrado em `.claude/settings.json`. Script `git_branch_guard.py` (stdlib only, sem dependência externa, shebang `#!/usr/bin/env python3` — chamado direto por path, sem prefixar `python3` no comando do hook).

## Três camadas, todas via o mesmo hook

1. **Sempre bloqueado, qualquer branch, qualquer repo** (`alwaysBlocked` no config): `reset --hard`, `clean -f`, `push --force/-f/--force-with-lease`, `branch -D`, `tag -d`, `checkout --` (descarta arquivo), `restore` (exceto `--staged`), `filter-branch`, `submodule deinit` — comandos com perda de dado sem recuperação fácil.
2. **Flag sempre bloqueada** (`blockedFlagsAnywhere`): `--no-verify` (pula hook de commit/push).
3. **Comando bloqueado só em branch protegida** (`blockedCommands` + `protectedBranches`): `commit`/`push` por padrão em `main`/`master`; liberado em qualquer outra branch.

## Como funciona

- Tokenizer via `shlex` (posix + `punctuation_chars`) faz split do comando em `;`/`&`/`&&`/`||`/`|` respeitando aspas — **limitação conhecida**: não trata newline (script multi-linha) nem `$(...)` (subshell) corretamente, isso pode escapar do parser.
- Resolve a branch/repo **alvo de cada invocação git** (não da sessão): extrai `-C <path>`/`--git-dir` de cada comando e checa a branch daquele repo, não do cwd do hook — então `git -C outro-repo commit` é avaliado contra a branch de `outro-repo`, não da sessão.
- Script auto-localiza o config (`hooks/config/git-guard.json`, relativo ao próprio arquivo via `Path(__file__)`); aceita override por arg1 ou `GIT_GUARD_CONFIG`.
- Config (`hooks/config/git-guard.json`): `protectedBranches`, `blockedCommands`, `exemptRepos` (caminhos absolutos onde a guardrail é totalmente desligada), `alwaysBlocked` (lista de `{subcommand, anyFlags?, unlessFlags?, firstArg?}`), `blockedFlagsAnywhere`.
- Nega com `permissionDecision: deny`, citando o motivo específico (branch protegida / comando destrutivo / flag bloqueada) e o path do config.
- Editar o JSON de config ou o script não exige nada além de já ter o hook carregado na sessão — sem build step, roda direto (requer `python3` no PATH).

## Testes

```bash
python3 hooks/git-branch-guard/test_git_branch_guard.py -v
```

Stdlib `unittest`, sem dependência — cobre parsing (`-C` encadeado, `--git-dir`, flags bundladas) e roda o config real (`hooks/config/git-guard.json`) contra um repo git descartável em `/tmp`.
