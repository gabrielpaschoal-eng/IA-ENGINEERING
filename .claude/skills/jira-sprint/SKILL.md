---
name: jira-sprint
description: Mostra os cards da sprint atual (ou de um status específico) de um board Jira configurado em settings/jira/boards.json. Use quando o usuário pedir "sprint atual", "board", "cards da sprint", "o que está em andamento no board X", ou mencionar um dos boards cadastrados em settings/jira/boards.json.
---

# Jira Sprint

Lista os issues da sprint em andamento de um board configurado neste harness, usando o MCP do Atlassian Rovo.

## Config

Board(s) cadastrados em `settings/jira/boards.json` (raiz do repo):

```json
{
  "cloudId": "...",
  "boards": [
    { "name": "...", "projectKey": "..." }
  ]
}
```

Pra cadastrar um board novo, adicione um objeto `{ "name": "...", "projectKey": "..." }` na lista `boards`. Todos os boards cadastrados compartilham o mesmo `cloudId` (site Atlassian do grupo).

`settings/jira/boards.json` é local (gitignored) — cada pessoa cadastra os próprios boards, não é compartilhado via git.

## Passos

1. Confira se `settings/jira/boards.json` existe na raiz do repo.
   - Se **não existir**: resolva o `cloudId` chamando `getAccessibleAtlassianResources` (se vier mais de um site, pergunte ao usuário qual usar). Crie o arquivo com `{ "cloudId": "<resolvido>", "boards": [] }`.
   - Avise o usuário que nenhum board estava cadastrado, pergunte o nome do board e a project key do Jira, adicione `{ "name": "...", "projectKey": "..." }` em `boards` e grave o arquivo antes de continuar.
2. Leia `settings/jira/boards.json` na raiz do repo.
3. Resolva qual board usar:
   - Se o usuário citou um nome de board ou uma project key no pedido (ou como argumento do skill), dê match (case-insensitive, substring) contra `boards[].name` / `boards[].projectKey`.
   - Se não citou e só existe 1 board configurado, use esse direto.
   - Se não citou e existem 2+ boards, pergunte ao usuário qual board usar (`AskUserQuestion`) antes de continuar.
4. Garanta que o MCP do Atlassian Rovo está autenticado nesta sessão (procure `mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql` via `ToolSearch`). Se a chamada retornar pedindo autenticação, instrua o usuário a rodar `/mcp` e selecionar "claude.ai Atlassian Rovo".
5. Chame `searchJiraIssuesUsingJql` com:
   - `cloudId`: valor de `settings/jira/boards.json`
   - `jql`: `project = <projectKey> AND sprint in openSprints() ORDER BY status ASC`
   - `maxResults`: 50
   - `fields`: `["summary", "status", "issuetype", "assignee"]` — **sempre restrinja os fields**; sem isso o retorno inclui descrição completa de cada issue e passa do limite de tokens da tool call.
6. Apresente os issues agrupados por status (colunas do board), formato tabela: chave (com link `webUrl`), resumo, tipo, responsável. Se algum status vier vazio, omita a seção.
7. Se a sprint atual não tiver nenhum issue (`openSprints()` vazio), avise que não há sprint ativa pro board — não invente dados.

## Notas

- `sprint in openSprints()` só funciona em projetos Scrum (com sprint). Todos os boards cadastrados hoje são Scrum.
- Não cachear/hardcodar o id da sprint — `openSprints()` já resolve a sprint corrente dinamicamente a cada chamada.
