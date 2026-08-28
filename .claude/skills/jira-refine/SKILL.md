---
name: jira-refine
description: Gera refinamento de negócio e técnico de uma task Jira, usando Serena pra mapear impacto no código real. Vincula automaticamente issue Jira ao repo local via settings/jira/links.json. Use quando o usuário pedir "refinar essa task", "refinamento da issue X", "vincular esse repo à task Y", ou citar uma issue key pra refinar.
---

# Jira Refine

Gera, a partir de uma issue Jira, um refinamento de negócio e depois um refinamento técnico (usando Serena pra mapear o impacto no código real do repositório), com pontos de clarificação com o usuário quando necessário. Tudo fica salvo como cache local — nenhum dado volta pro Jira.

**Propósito**: virar o ponto de partida pra começar o desenvolvimento (ou delegar a task pra um agente) já com contexto de negócio + técnico mastigado — não é um artefato pro Jira, é um artefato pro harness.

**Regra dura — somente leitura no Jira.** Esta skill nunca chama tool de escrita do Atlassian Rovo (`editJiraIssue`, `addCommentToJiraIssue`, `createIssueLink`, `transitionJiraIssue`, `addWorklogToJiraIssue`, etc.) — nem na task nem no épico. A única chamada ao Jira é leitura (`getJiraIssue`). Todo output (refinamentos, clarificações, vínculo repo↔issue) fica exclusivamente em cache local (`settings/jira/`).

## Config

- `settings/jira/boards.json` (raiz do repo, gitignored, mesmo arquivo usado pela skill `jira-sprint`): guarda `cloudId`. Reaproveitar esse arquivo — não duplicar a lógica de resolução de `cloudId`. Se ainda não existir, faça o mesmo bootstrap da skill `jira-sprint` (resolve `cloudId` via `getAccessibleAtlassianResources`, perguntando ao usuário se vier mais de um site).
- `settings/jira/links.json` (raiz do repo, gitignored — local, não compartilhado via git): mapeia repositório local → issue key.

  ```json
  {
    "links": [
      { "repoPath": "/caminho/absoluto/do/repo", "issueKey": "DA-123" }
    ]
  }
  ```

  `repoPath` é o toplevel do repo (`git rev-parse --show-toplevel`), pra casar com qualquer subpasta de onde a skill for chamada.

- `settings/jira/refinements/<CARD_KEY>/` (raiz do repo, gitignored): cache dos refinamentos gerados, um arquivo por etapa:
  - `raw.json` — issue + comentários como vieram do Jira.
  - `business.md` — refinamento de negócio.
  - `technical.md` — refinamento técnico.
  - `final-<uuid>.md` — consolidado das duas etapas.

## Passos

1. **Resolver issue key e vínculo repo↔issue**
   - Se o usuário passou uma issue key (argumento do skill ou citada no pedido), use-a diretamente.
   - Caso contrário, leia `settings/jira/links.json` (se existir) e procure uma entrada cujo `repoPath` bata com `git rev-parse --show-toplevel` do repositório atual. Se achar, use esse `issueKey`.
   - Se não achar nenhuma das duas formas, pergunte a issue key ao usuário.
   - Se a issue key veio do argumento/pedido do usuário (não do `links.json`) e ainda não existe entrada para esse `repoPath`, pergunte se quer salvar o vínculo para as próximas vezes. Se sim: crie `settings/jira/links.json` com `{"links": []}` caso não exista, depois faça append da entrada e regrave.
   - Resolva o `cloudId` via `settings/jira/boards.json` (ver seção Config).

2. **Fetch (raw)**
   - Use `ToolSearch` para localizar `getJiraIssue`. Se a chamada pedir autenticação, instrua o usuário a rodar `/mcp` e selecionar "claude.ai Atlassian Rovo".
   - Chame `getJiraIssue` com `cloudId`, `issueIdOrKey=<ISSUE-KEY>` e `fields` restrito a `["summary", "description", "comment", "status", "issuetype"]` — nunca peça o objeto completo, estoura o orçamento de contexto.
   - Crie `settings/jira/refinements/<CARD_KEY>/` se não existir. Grave o retorno em `raw.json`.

3. **Refinamento de negócio**
   - Leia `raw.json` e sintetize em `business.md`: contexto de negócio, regras, critérios de aceite, edge cases citados nos comentários.

4. **Clarify de negócio (condicional)**
   - Revise `business.md` procurando ambiguidade genuína (algo que a issue/comentários realmente deixam em aberto) — não invente pergunta por inventar.
   - Se achar lacuna, use `AskUserQuestion` e atualize `business.md` com a resposta antes de seguir. Se não achar nada, siga direto.

5. **Refinamento técnico (Serena)**
   - Resolva o repositório alvo: o `repoPath` vinculado, ou o repositório onde a sessão já está rodando.
   - Chame `mcp__serena__initial_instructions` e depois `mcp__serena__activate_project` nesse repositório (nunca no `TOOLS/`).
   - Use `find_symbol`, `find_referencing_symbols`, `get_symbols_overview` para mapear módulos/arquivos relacionados ao domínio descrito em `business.md`.
   - Grave `technical.md`: abordagem técnica, arquivos/módulos impactados, riscos.

6. **Clarify técnico (condicional)**
   - Só pergunte se `technical.md` apontar 2+ abordagens igualmente válidas ou uma dependência externa incerta. Use `AskUserQuestion` e atualize `technical.md` com a resposta. Não repita perguntas já resolvidas na etapa de negócio.

7. **Consolidar**
   - Gere um uuid: `python3 -c "import uuid;print(uuid.uuid4())"`.
   - Escreva `final-<uuid>.md` com: cabeçalho (card key, link da issue via `webUrl`, timestamp) seguido do conteúdo de `business.md` e `technical.md`.
   - Avise o usuário do caminho do arquivo final gerado.

## Notas

- Reaproveita `cloudId`/`boards.json` da skill `jira-sprint` — nunca duplicar essa lógica.
- Etapas 4 e 6 não são obrigatórias a cada rodada — só perguntam quando há lacuna/ambiguidade real, para não virar ruído.
- Repetir a skill na mesma issue gera um novo `final-<uuid>.md` (histórico preservado) — não sobrescreve o anterior. `raw.json`/`business.md`/`technical.md` são sobrescritos a cada rodada (representam o estado mais recente do refinamento).
