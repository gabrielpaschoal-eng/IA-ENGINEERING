# TOOLS Harness

Harness pessoal do time IA AUTOMATION: Claude Code como motor, plugado nos repositórios do dia a dia. Sessão sempre aberta a partir desta pasta; outros repositórios entram via `--add-dir` / `additionalDirectories`.

## Regras

- Tudo que for criado para o harness (hooks, scripts, config, skills) fica dentro desta pasta (`TOOLS/`). Nada em `~/.claude/` — só o registro mínimo que já vem por padrão.
- Config geral do harness (fora do escopo específico de um hook) fica em `settings/`, organizada por integração/subsistema (ex.: `settings/jira/`).

## Estrutura

```
TOOLS/
├── claude.md                      # este arquivo
├── .gitignore                     # ignora config local (settings/jira/boards.json, settings/jira/links.json, settings/jira/refinements/, settings/serena/.env, etc.) e __pycache__/
├── .mcp.json                       # registro do MCP Serena (project-scope, versionado)
├── .claude/settings.json          # registro dos hooks (project-level)
├── hooks/
│   ├── git-branch-guard/
│   │   └── git_branch_guard.py    # hook PreToolUse/Bash (Python, stdlib only, executável direto)
│   ├── serena-reminder/
│   │   └── serena_reminder.py     # hook SessionStart: lembra de usar mcp__serena__* em código real
│   └── config/git-guard.json      # config da guardrail de git
├── settings/                      # configs do harness (por integração/subsistema)
│   ├── jira/boards.json           # boards Jira do usuário (cloudId + projectKey) — gitignored, criado pela skill no 1º uso
│   ├── jira/links.json            # vínculo repo local ↔ issue key — gitignored, criado pela skill jira-refine no 1º uso
│   ├── jira/refinements/          # cache dos refinamentos gerados por issue — gitignored, criado pela skill jira-refine
│   └── serena/                    # docker-compose do MCP Serena (config/.env locais são gitignored)
├── knowledge/                      # conteúdo compartilhado de boas práticas (DDD, SOLID, Clean Architecture/Code, Design Patterns, Database, refinamento, negócio) — não é skill, só .md, referenciado pelas skills practices-*
├── .claude/skills/jira-sprint/     # skill que lê/cria settings/jira/boards.json e consulta a sprint atual
├── .claude/skills/jira-refine/     # skill que gera refinamento de negócio/técnico de uma issue (leitura only no Jira)
├── .claude/skills/practices-code/         # skill roteadora: aplica knowledge/{ddd,solid,clean-architecture,clean-code,design-patterns,database}.md
├── .claude/skills/practices-refinement/   # skill roteadora: aplica knowledge/refinement.md
└── .claude/skills/practices-business/     # skill roteadora: aplica knowledge/business.md
```

## Guardrails

### Git — bloqueio de comando em branch protegida

Criar branch é sempre livre. Comandos configurados (`commit`, `push` por padrão) são bloqueados quando a branch atual está na lista de protegidas (`main`/`master` por padrão); liberado em qualquer outra branch.

- Hook `PreToolUse` (matcher `Bash`) registrado em `.claude/settings.json`, script Python em `hooks/git-branch-guard/git_branch_guard.py` (stdlib only, sem dependência externa, executável via shebang `#!/usr/bin/env python3` — chamado direto por path, sem prefixar `python3` no comando do hook).
- Tokenizer via `shlex` (posix + `punctuation_chars`) faz split do comando em `;`/`&`/`&&`/`||`/`|`/subshell respeitando aspas, e resolve o subcomando git ignorando flags globais (`-C`, `-c`, etc.) e prefixos de env var (`FOO=bar git ...`).
- Script auto-localiza o config (`hooks/config/git-guard.json`, relativo ao próprio arquivo via `Path(__file__)`); aceita override por arg1 ou `GIT_GUARD_CONFIG`.
- Config (`hooks/config/git-guard.json`):
  - `protectedBranches`: branches bloqueadas
  - `blockedCommands`: subcomandos git bloqueados nessas branches
  - `exemptRepos`: caminhos absolutos (toplevel do repo) onde a guardrail é totalmente desligada
- Checa a branch atual (`git rev-parse --abbrev-ref HEAD`) do repo onde a sessão está rodando — não do repo alvo do comando — antes de deixar os comandos configurados passarem; nega com `permissionDecision: deny` citando a branch e o path do config.
- Editar o JSON de config ou o script não exige nada além de já ter o hook carregado na sessão — sem build step, roda direto (requer `python3` no PATH).

## Integrações

### Jira — sprint atual por board

- Boards cadastrados em `settings/jira/boards.json` (raiz, gitignored — config local, não compartilhado via git): `{ "cloudId": "...", "boards": [{ "name": "...", "projectKey": "..." }] }`. Todos os boards de um mesmo arquivo compartilham o `cloudId` (site Atlassian do grupo).
- Skill `jira-sprint` (`.claude/skills/jira-sprint/SKILL.md`) lê esse config, resolve o board (por nome/project key citado, ou pergunta se houver mais de um cadastrado) e consulta a sprint em andamento via MCP do Atlassian Rovo (`project = <key> AND sprint in openSprints()`).
- Se `settings/jira/boards.json` não existir, a skill cria (resolvendo `cloudId` via `getAccessibleAtlassianResources`) e pergunta o primeiro board pra cadastrar — cada pessoa que usar o harness cadastra os próprios boards no primeiro uso.
- Requer autenticação do MCP "claude.ai Atlassian Rovo" ativa na sessão (`/mcp` pra logar).
- Adicionar board novo: só editar `settings/jira/boards.json` (ou pedir pra skill cadastrar), sem tocar na skill.

### Jira — refinamento de task (jira-refine)

- Skill `jira-refine` (`.claude/skills/jira-refine/SKILL.md`) vincula o repo local a uma issue Jira (`settings/jira/links.json`, gitignored: `{ "links": [{ "repoPath": "...", "issueKey": "...", "outputDir": "..." }] }`) e gera, a partir da issue + comentários (e páginas Confluence citadas nelas, se houver), um refinamento de negócio e depois um técnico (usando Serena — `activate_project` no repo alvo, `find_symbol`/`find_referencing_symbols`/`get_symbols_overview` — pra mapear módulos/arquivos impactados), com clarificação pontual (`AskUserQuestion`) só quando sobra ambiguidade real.
- `outputDir` na entrada de `links.json` é opcional e por repo/link: se ausente, cache vai pro default (`settings/jira/refinements/<CARD_KEY>/` dentro do `TOOLS/`); se presente, vai pra `<outputDir>/<CARD_KEY>/` (ex.: dentro do próprio repo alvo). Se apontar pra fora do `TOOLS/`, o `.gitignore` daquele destino é responsabilidade de quem configurou — a skill não mexe em `.gitignore` de outros repos.
- Antes de buscar no Jira, checa se já existe refinamento pra issue (compara `updated` salvo em `raw.json` contra o atual) e, se nada mudou, oferece reabrir o `final-<uuid>.md` mais recente em vez de rodar tudo de novo.
- Reaproveita `cloudId`/`boards.json` da skill `jira-sprint` — não duplica resolução de `cloudId`.
- Cache dos refinamentos no diretório resolvido (padrão ou `outputDir`): `raw.json`, `confluence.md` (se houver link citado), `business.md`, `technical.md`, `final-<uuid>.md` (com checklist de implementação ao final — histórico preservado, cada rodada gera um novo `final-<uuid>.md`).
- **Somente leitura no Jira** — a skill nunca chama tool de escrita do Atlassian Rovo (`editJiraIssue`, `addCommentToJiraIssue`, `createIssueLink`, `transitionJiraIssue`, etc.), nem na task nem no épico. O refinamento é um artefato pro harness/agente (ponto de partida pra desenvolver ou delegar a task), não um artefato pro Jira.
- Mesma exigência de auth do MCP Atlassian Rovo da `jira-sprint` (Confluence usa o mesmo conector).

### Boas práticas (knowledge/ + skills de prática)

- `knowledge/*.md`: conteúdo compartilhado, não é skill — cada arquivo é um checklist prático (regra, sintoma de violação, direção do fix) de um tópico: `ddd.md`, `solid.md`, `clean-architecture.md`, `clean-code.md`, `design-patterns.md`, `database.md`, `refinement.md`, `business.md`.
- `knowledge/technical-refinement-template.md`: estrutura ADR-lite (contexto, decisão recomendada, alternativas consideradas e por que foram descartadas, componentes impactados, diagrama, riscos & mitigação, rollout/reversibilidade, requisitos não-funcionais, dependências, alçada) pra quando o refinamento técnico é entregue pro time decidir/revisar, não só pra uso pessoal — usado por `practices-code` e pela etapa técnica do `jira-refine`.
- 3 skills roteadoras leem esse conteúdo sob demanda (progressive disclosure — o `SKILL.md` fica fino, o conteúdo pesado vive separado):
  - `practices-code` (`.claude/skills/practices-code/SKILL.md`): DDD, SOLID, Clean Architecture, Clean Code, Design Patterns, Database.
  - `practices-refinement` (`.claude/skills/practices-refinement/SKILL.md`): formato/testabilidade de critério de aceite.
  - `practices-business` (`.claude/skills/practices-business/SKILL.md`): modelagem/linguagem de negócio.
- Cada uma funciona **standalone** (dispara por pedido explícito, ex. "revisa esse código com SOLID") **e** é invocada internamente pelo `jira-refine`: `practices-business`/`practices-refinement` na etapa de refinamento de negócio, `practices-code` na etapa de refinamento técnico.
- Guarda contra ruído: cada skill tem `## Quando aplicar` / `## Quando não aplicar` no corpo — não deveria disparar (nem sozinha nem forçar checklist inteiro) num fix pontual de poucas linhas.
- Adicionar tópico novo: só criar o `.md` em `knowledge/` e referenciar na tabela da skill roteadora correspondente — não precisa nova skill.

### Serena — navegação semântica de código (MCP)

Ferramentas de navegação/edição via LSP (`find_symbol`, `find_referencing_symbols`, `replace_symbol_body`, etc.) e memória por projeto (`write_memory`/`read_memory`), pra usar nos repositórios de trabalho reais plugados via `--add-dir` — não faz sentido pro `TOOLS/` em si (base pequena demais pra LSP compensar).

- Roda via Docker, imagem oficial `ghcr.io/oraios/serena:latest` direto (sem Dockerfile próprio), transporte SSE na porta 9121 (dashboard web na 24282). Healthcheck no compose bate em `http://127.0.0.1:24282/dashboard/index.html` **de dentro do container** (o dashboard só escuta em loopback interno — não dá pra checar isso do host) — `docker compose ps` mostra `(healthy)`/`(unhealthy)` em vez de só "Up".
- Cobertura de linguagem: das stacks que usamos (Go, TypeScript, Java, Python), a imagem oficial cobre TS e Java de cara (baixam o language server sozinhos na primeira ativação — npm / bundle com JRE embutido) e Python já funciona (`uv` já vem na imagem). **Go não funciona** nessa imagem — `gopls` exigiria toolchain Go pré-instalado, que a imagem oficial não tem; decidimos não manter um Dockerfile próprio pra isso (custo de manutenção > ganho), então navegação semântica em projeto Go fica sem suporte por enquanto.
- Setup por máquina: copiar `settings/serena/.env.example` pra `settings/serena/.env` e ajustar `SERENA_PROJECTS_DIR` (diretório pai que contém os repos que você quer que o Serena acesse — montado como `/workspace` dentro do container). `.env` e `config/` são locais/gitignored (cada pessoa tem seu próprio path e sua própria config/memórias).
- Subir: `cd settings/serena && docker compose up -d`. Se seu usuário não estiver no grupo `docker` (comum com o snap do Docker/Ubuntu), ver **Notas operacionais**.
- Registro no Claude Code é automático via `.mcp.json` (raiz do repo, versionado — `url` é `http://localhost:${SERENA_PORT:-9121}/sse`, mesmo default do `docker-compose.yml`). Ninguém precisa rodar `claude mcp add` manualmente: ao abrir o harness, o Claude Code pede aprovação de confiança do servidor **uma vez por máquina** (`claude mcp list` mostra `⏸ Pending approval` até aceitar — some ao rodar `claude` de novo e aprovar o prompt). Requer o container do Serena já rodando (`docker compose up -d`) antes de aprovar/usar.
- **Pegadinha do `${SERENA_PORT}`**: o Claude Code não lê `.env` sozinho pra expandir isso — só enxerga variável já exportada no shell antes de rodar `claude` (diferente do `docker compose`, que lê `settings/serena/.env` automático). Funciona sem nada extra enquanto a porta for a default (`9121`, igual nos dois lugares). Se customizar `SERENA_PORT` em `settings/serena/.env`, precisa também `export SERENA_PORT=<valor>` no shell antes de abrir a sessão, senão o `.mcp.json` cai no default enquanto o container sobe noutra porta.
- `claude mcp reset-project-choices` reseta a aprovação (útil se o `.mcp.json` mudar e precisar reconfiar).
- Ao ativar um projeto pela primeira vez (`activate_project` / onboarding do Serena), ele grava memórias daquele repo em `.serena/memories/` dentro do próprio repo de trabalho (não dentro do `TOOLS/`).
- Hook `SessionStart` (matcher `startup`, `hooks/serena-reminder/serena_reminder.py`) injeta lembrete de contexto toda vez que uma sessão nova abre neste harness: usar `mcp__serena__*` (não `Read`/`Grep`) pra navegação/edição de código real, e chamar `initial_instructions`/`activate_project` antes de começar uma tarefa de código num repo. Sem isso, nada garante que eu de fato uso as ferramentas do Serena em vez de cair no hábito.

## Notas operacionais

- Hook novo ou `.claude/settings.json` editado no meio da sessão exige rodar `/hooks` uma vez (ou reiniciar a sessão) pra recarregar.
- Hooks são scripts Python (stdlib only) executados direto por path — sem build step.
- MCP de `.mcp.json` (project-scope, ex.: Serena) pede aprovação de confiança na primeira vez que a sessão abre nesse repo (`⏸ Pending approval` em `claude mcp list` até aceitar) — reiniciar `claude` e aprovar o prompt. MCP registrado em outro scope no meio da sessão só aparece depois de `/mcp` (reload).
- Docker via snap (comum em Ubuntu) não cria o grupo `docker` sozinho: `sudo addgroup --system docker && sudo adduser $USER docker && sudo snap disable docker && sudo snap enable docker`, depois logout/login (ou `newgrp docker`/`sg docker -c "..."` pra testar sem relogar).
