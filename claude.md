# TOOLS Harness

Harness pessoal do time IA AUTOMATION: Claude Code como motor, plugado nos repositórios do dia a dia. Sessão sempre aberta a partir desta pasta; outros repositórios entram via `--add-dir` / `additionalDirectories`.

## Regras

- Tudo que for criado para o harness (hooks, scripts, config, skills) fica dentro desta pasta (`TOOLS/`). Nada em `~/.claude/` — só o registro mínimo que já vem por padrão.
- Config geral do harness (fora do escopo específico de um hook) fica em `settings/`, organizada por integração/subsistema (ex.: `settings/jira/`).

## Estrutura

```
TOOLS/
├── claude.md                      # este arquivo
├── Makefile                       # builda todos os hooks Go (hooks/*/main.go -> hooks/bin/*)
├── .gitignore                     # ignora binário compilado (hooks/bin/) e config local (settings/settings/jira/boards.json)
├── .claude/settings.json          # registro dos hooks (project-level)
├── hooks/
│   ├── git-branch-guard/          # fonte Go (main.go, go.mod)
│   ├── bin/git-branch-guard       # binário compilado (gitignored, gerado localmente)
│   └── config/git-guard.json      # config da guardrail de git
├── settings/                      # configs do harness (por integração/subsistema)
│   └── settings/jira/boards.json           # boards Jira do usuário (cloudId + projectKey) — gitignored, criado pela skill no 1º uso
└── .claude/skills/jira-sprint/     # skill que lê/cria settings/settings/jira/boards.json e consulta a sprint atual
```

## Guardrails

### Git — bloqueio de comando em branch protegida

Criar branch é sempre livre. Comandos configurados (`commit`, `push` por padrão) são bloqueados quando a branch atual está na lista de protegidas (`main`/`master` por padrão); liberado em qualquer outra branch.

- Hook `PreToolUse` (matcher `Bash`) registrado em `.claude/settings.json`, binário Go em `hooks/bin/git-branch-guard` (fonte em `hooks/git-branch-guard/main.go`).
- Tokenizer próprio (stdlib, sem dependência externa) faz split do comando em `;`/`&`/`&&`/`||`/`|`/subshell respeitando aspas, e resolve o subcomando git ignorando flags globais (`-C`, `-c`, etc.) e prefixos de env var (`FOO=bar git ...`). Mais robusto que regex simples.
- Binário auto-localiza o config (`hooks/config/git-guard.json`, relativo ao próprio executável) via `os.Executable()`; aceita override por arg1 ou `GIT_GUARD_CONFIG`.
- Config (`hooks/config/git-guard.json`):
  - `protectedBranches`: branches bloqueadas
  - `blockedCommands`: subcomandos git bloqueados nessas branches
  - `exemptRepos`: caminhos absolutos (toplevel do repo) onde a guardrail é totalmente desligada
- Checa a branch atual (`git rev-parse --abbrev-ref HEAD`) do repo onde a sessão está rodando — não do repo alvo do comando — antes de deixar os comandos configurados passarem; nega com `permissionDecision: deny` citando a branch e o path do config.
- Editar o JSON de config não exige nada além de já ter o hook carregado na sessão.
- Rebuild após mudar `main.go`: `make git-branch-guard` (ou `make` pra buildar todos os hooks).

## Build dos hooks

`Makefile` na raiz detecta automaticamente todo diretório em `hooks/` com `main.go` + `go.mod` — nenhum target novo precisa ser escrito manualmente ao adicionar um hook.

- `make` / `make build-all`: builda todos os hooks Go pra `hooks/bin/<nome>`
- `make <nome>` (ex.: `make git-branch-guard`): builda só um hook
- `make clean`: remove `hooks/bin`

## Integrações

### Jira — sprint atual por board

- Boards cadastrados em `settings/jira/boards.json` (raiz, gitignored — config local, não compartilhado via git): `{ "cloudId": "...", "boards": [{ "name": "...", "projectKey": "..." }] }`. Todos os boards de um mesmo arquivo compartilham o `cloudId` (site Atlassian do grupo).
- Skill `jira-sprint` (`.claude/skills/jira-sprint/SKILL.md`) lê esse config, resolve o board (por nome/project key citado, ou pergunta se houver mais de um cadastrado) e consulta a sprint em andamento via MCP do Atlassian Rovo (`project = <key> AND sprint in openSprints()`).
- Se `settings/jira/boards.json` não existir, a skill cria (resolvendo `cloudId` via `getAccessibleAtlassianResources`) e pergunta o primeiro board pra cadastrar — cada pessoa que usar o harness cadastra os próprios boards no primeiro uso.
- Requer autenticação do MCP "claude.ai Atlassian Rovo" ativa na sessão (`/mcp` pra logar).
- Adicionar board novo: só editar `settings/jira/boards.json` (ou pedir pra skill cadastrar), sem tocar na skill.

## Notas operacionais

- Hook novo ou `.claude/settings.json` editado no meio da sessão exige rodar `/hooks` uma vez (ou reiniciar a sessão) pra recarregar.
- Mudança no fonte Go de um hook exige rebuild do binário (ver seção Build acima) — o hook chama o binário direto, não recompila em runtime.
