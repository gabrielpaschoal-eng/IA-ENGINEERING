# TOOLS Harness

Harness pessoal do time IA AUTOMATION: Claude Code como motor, plugado nos repositórios do dia a dia. Sessão sempre aberta a partir desta pasta; outros repositórios entram via `--add-dir` / `additionalDirectories`.

## Regras

- Tudo que for criado para o harness (hooks, scripts, config, skills) fica dentro desta pasta (`TOOLS/`). Nada em `~/.claude/` — só o registro mínimo que já vem por padrão.
- Config geral do harness (fora do escopo específico de um hook) fica em `settings/`, organizada por integração/subsistema (ex.: `settings/jira/`).
- Cada hook/skill/setup mais complexo tem seu próprio `README.md` no diretório (detalhe de implementação, gotchas, testes) — este arquivo é o índice, não repete esse conteúdo. Ao mexer num hook/skill, abra o `README.md`/`SKILL.md` dele antes de assumir como funciona.

## Estrutura

```
TOOLS/
├── claude.md                      # este arquivo (índice)
├── .gitignore                     # ignora config local (settings/jira/boards.json, settings/jira/links.json, settings/jira/refinements/, settings/serena/.env, etc.) e __pycache__/
├── .mcp.json                       # registro do MCP Serena (project-scope, versionado)
├── .claude/settings.json          # registro dos hooks (project-level)
├── hooks/
│   ├── git-branch-guard/          # guardrail de git — detalhe em hooks/git-branch-guard/README.md
│   ├── jira-write-guard/          # guardrail de escrita no Jira — detalhe em hooks/jira-write-guard/README.md
│   ├── serena-reminder/           # hook SessionStart: lembra de usar mcp__serena__* em código real
│   └── config/                    # git-guard.json, jira-write-guard.json
├── settings/                      # configs do harness (por integração/subsistema)
│   ├── jira/boards.json           # boards Jira do usuário — gitignored, criado pela skill no 1º uso
│   ├── jira/links.json            # vínculo repo local ↔ issue key — gitignored, criado pela skill jira-refine
│   ├── jira/refinements/          # cache dos refinamentos gerados por issue — gitignored
│   └── serena/                    # docker-compose do MCP Serena — setup em settings/serena/README.md
├── knowledge/                      # conteúdo compartilhado de boas práticas (DDD, SOLID, Clean Architecture/Code, Design Patterns, Database, refinamento, negócio) — não é skill, referenciado pelas skills practices-*
├── .claude/skills/jira-sprint/     # skill: sprint atual de um board — detalhe no SKILL.md
├── .claude/skills/jira-refine/     # skill: refinamento de negócio/técnico de uma issue — detalhe no SKILL.md
├── .claude/skills/practices-code/         # skill roteadora de knowledge/{ddd,solid,clean-architecture,clean-code,design-patterns,database}.md
├── .claude/skills/practices-refinement/   # skill roteadora de knowledge/refinement.md
└── .claude/skills/practices-business/     # skill roteadora de knowledge/business.md
```

## Guardrails

### Git — bloqueio de comando destrutivo / branch protegida

Hook `PreToolUse`/`Bash` (`hooks/git-branch-guard/git_branch_guard.py`, config `hooks/config/git-guard.json`) bloqueia em 3 camadas: comando destrutivo sempre (`reset --hard`, `push --force`, `branch -D`, etc.), flag `--no-verify` sempre, e `commit`/`push` só em branch protegida (`main`/`master` por padrão) — liberado em qualquer outra branch. Criar branch é sempre livre.

Detalhe (tokenizer, resolução de `-C`/`--git-dir`, limitação conhecida, testes): **`hooks/git-branch-guard/README.md`**.

### Jira — bloqueio de escrita em task/épico

Hook `PreToolUse`/`mcp__.*Atlassian.*` (`hooks/jira-write-guard/jira_write_guard.py`, config `hooks/config/jira-write-guard.json`) nega qualquer chamada MCP que edite/comente/transicione issue do Jira — reforça a nível técnico a regra "somente leitura" da skill `jira-refine`. Confluence fica de fora (escrita opt-in dessa skill).

Detalhe: **`hooks/jira-write-guard/README.md`**.

## Integrações

### Jira — sprint atual por board (`jira-sprint`)

Lista os cards da sprint em andamento de um board cadastrado em `settings/jira/boards.json` (`cloudId` + `projectKey`, gitignored, criado no 1º uso). Requer MCP "claude.ai Atlassian Rovo" autenticado (`/mcp`).

Detalhe completo: **`.claude/skills/jira-sprint/SKILL.md`**.

### Jira — refinamento de task (`jira-refine`)

Vincula repo local a uma issue (`settings/jira/links.json`) e gera refinamento de negócio + técnico (via Serena) em cache local (`settings/jira/refinements/<CARD_KEY>/`), com clarificação pontual e publicação opcional no Confluence. Reaproveita `cloudId`/`boards.json` da `jira-sprint`. Nunca escreve na task/épico do Jira (reforçado pelo hook acima).

Detalhe completo (todas as etapas, schema de config, formato do cache): **`.claude/skills/jira-refine/SKILL.md`**.

### Boas práticas (`knowledge/` + skills `practices-*`)

`knowledge/*.md` guarda checklists práticos por tópico (DDD, SOLID, Clean Architecture, Clean Code, Design Patterns, Database, refinamento, negócio, template de refinamento técnico). Três skills roteadoras (`practices-code`, `practices-refinement`, `practices-business`) leem esse conteúdo sob demanda — funcionam standalone (disparo por pedido explícito) e são invocadas internamente pelo `jira-refine`. Tópico novo = novo `.md` em `knowledge/` + linha na tabela da skill correspondente, sem criar skill nova.

Detalhe de cada roteadora (quando aplica/não aplica, tabela de tópicos): `.claude/skills/practices-*/SKILL.md`.

### Serena — navegação semântica de código (MCP)

LSP (`find_symbol`, `find_referencing_symbols`, etc.) e memória por projeto, via Docker, pra repositórios de trabalho reais plugados via `--add-dir` — não pro `TOOLS/` em si. Hook `SessionStart` (`hooks/serena-reminder/serena_reminder.py`) lembra de usar `mcp__serena__*` e chamar `initial_instructions`/`activate_project` antes de codar num repo real.

Setup completo (subir container, registro no Claude Code, cobertura de linguagem, gotchas): **`settings/serena/README.md`**.

## Notas operacionais

- Hook novo ou `.claude/settings.json` editado no meio da sessão exige rodar `/hooks` uma vez (ou reiniciar a sessão) pra recarregar.
- Hooks são scripts Python (stdlib only) executados direto por path — sem build step.
- MCP de `.mcp.json` (project-scope, ex.: Serena) pede aprovação de confiança na primeira vez que a sessão abre nesse repo (`⏸ Pending approval` em `claude mcp list` até aceitar). MCP registrado em outro scope no meio da sessão só aparece depois de `/mcp` (reload).
