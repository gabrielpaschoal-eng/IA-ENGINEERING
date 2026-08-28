# TOOLS Harness

Harness pessoal do time IA AUTOMATION: Claude Code como motor, plugado nos repositórios do dia a dia. Sessão sempre aberta a partir desta pasta; outros repositórios entram via `--add-dir` / `additionalDirectories`.

## Regras

- Tudo que for criado para o harness (hooks, scripts, config, skills) fica dentro desta pasta (`TOOLS/`). Nada em `~/.claude/` — só o registro mínimo que já vem por padrão.

## Estrutura

```
TOOLS/
├── claude.md                      # este arquivo
├── .claude/settings.json          # registro dos hooks (project-level)
└── hooks/
    ├── git-branch-guard.sh        # guardrail de git
    └── config/git-guard.json      # config da guardrail de git
```

## Guardrails

### Git — bloqueio de comando em branch protegida

Criar branch é sempre livre. Comandos configurados (`commit`, `push` por padrão) são bloqueados quando a branch atual está na lista de protegidas (`main`/`master` por padrão); liberado em qualquer outra branch.

- Hook `PreToolUse` (matcher `Bash`) registrado em `.claude/settings.json`, script em `hooks/git-branch-guard.sh`.
- Script auto-localiza o config (`hooks/config/git-guard.json`) via `BASH_SOURCE`, funciona mesmo chamado de outro diretório.
- Config (`hooks/config/git-guard.json`):
  - `protectedBranches`: branches bloqueadas
  - `blockedCommands`: subcomandos git bloqueados nessas branches
  - `exemptRepos`: caminhos absolutos (toplevel do repo) onde a guardrail é totalmente desligada
- Checa a branch atual (`git rev-parse --abbrev-ref HEAD`) antes de deixar os comandos configurados passarem; nega com `permissionDecision: deny` citando a branch e o path do config.
- Editar o JSON de config não exige nada além de já ter o hook carregado na sessão.

## Notas operacionais

- Hook novo ou `.claude/settings.json` editado no meio da sessão exige rodar `/hooks` uma vez (ou reiniciar a sessão) pra recarregar.
