# jira-write-guard

Hook `PreToolUse` (matcher `mcp__.*Atlassian.*`) registrado em `.claude/settings.json`. Nega qualquer chamada MCP cujo nome termine num sufixo de `blockedToolSuffixes` (`hooks/config/jira-write-guard.json`): `createJiraIssue`, `editJiraIssue`, `addCommentToJiraIssue`, `addWorklogToJiraIssue`, `createIssueLink`, `transitionJiraIssue`.

## Por quê

Torna técnica (bloqueio a nível de hook) a regra que antes só existia como instrução de prosa na skill `jira-refine` ("nunca escreve no Jira") — defesa em profundidade contra alucinação ou instrução maliciosa vinda de um comentário de issue.

## Detalhe

- Casa por **sufixo** do nome da tool (`tool_name.endswith(sufixo)`), não nome completo, pra sobreviver a troca de versão do conector MCP (ex.: `mcp__..._Atlassian_Rovo__X` vs `mcp__..._Atlassian_Rovo_2__X`).
- Confluence **não** está na lista (`createConfluencePage`/`updateConfluencePage` continuam liberados) — é a escrita opt-in da etapa 10 do `jira-refine`, intencional.
- Mesmo padrão de config do `git-branch-guard`: editar `blockedToolSuffixes` no JSON não exige nada além do hook já carregado na sessão.
