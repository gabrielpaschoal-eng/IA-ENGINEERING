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
- `settings/jira/links.json` (raiz do repo, gitignored — local, não compartilhado via git): mapeia repositório local → issue key, com destino opcional do refinamento.

  ```json
  {
    "links": [
      { "repoPath": "/caminho/absoluto/do/repo", "issueKey": "DA-123", "outputDir": "/caminho/opcional/onde/salvar" }
    ]
  }
  ```

  `repoPath` é o toplevel do repo (`git rev-parse --show-toplevel`), pra casar com qualquer subpasta de onde a skill for chamada. `outputDir` é opcional: se ausente, usa o default (`settings/jira/refinements/` na raiz do `TOOLS/`); se presente, os arquivos de cache vão pra `<outputDir>/<CARD_KEY>/` (por exemplo, dentro do próprio repo alvo — útil quando o refinamento é feito pra um agente que já vai trabalhar lá).

- Diretório de refinamento resolvido (`settings/jira/refinements/<CARD_KEY>/` por padrão, ou `<outputDir>/<CARD_KEY>/` se `outputDir` configurado): cache dos refinamentos gerados, um arquivo por etapa:
  - `raw.json` — issue + comentários como vieram do Jira, incluindo `status`/`updated` (usado na checagem de atualidade da etapa 2).
  - `confluence.md` — conteúdo de páginas Confluence citadas na descrição/comentários, se houver (arquivo omitido quando nenhum link é encontrado).
  - `business.md` — refinamento de negócio.
  - `technical.md` — refinamento técnico.
  - `final-<uuid>.md` — consolidado das etapas + checklist acionável.

## Passos

1. **Resolver issue key e vínculo repo↔issue**
   - Se o usuário passou uma issue key (argumento do skill ou citada no pedido), use-a diretamente.
   - Caso contrário, leia `settings/jira/links.json` (se existir) e procure uma entrada cujo `repoPath` bata com `git rev-parse --show-toplevel` do repositório atual. Se achar, use esse `issueKey`.
   - Se não achar nenhuma das duas formas, pergunte a issue key ao usuário.
   - Se a issue key veio do argumento/pedido do usuário (não do `links.json`) e ainda não existe entrada para esse `repoPath`, pergunte se quer salvar o vínculo para as próximas vezes (e, opcionalmente, um `outputDir` customizado). Se sim: crie `settings/jira/links.json` com `{"links": []}` caso não exista, depois faça append da entrada e regrave.
   - Resolva o `cloudId` via `settings/jira/boards.json` (ver seção Config) e o diretório de refinamento (`outputDir` da entrada, se houver, senão o default) — esse diretório é usado em todas as etapas seguintes.

2. **Checar refinamento existente (idempotência)**
   - Veja se já existe `raw.json` no diretório de refinamento resolvido na etapa 1.
   - Se não existir, siga direto pra etapa 3.
   - Se existir, chame `getJiraIssue` só com `fields=["status", "updated"]` (chamada leve) e compare `updated` com o valor salvo em `raw.json`.
   - Se `updated` for igual: a issue não mudou desde o último refinamento. Liste o `final-<uuid>.md` mais recente do diretório e use `AskUserQuestion` perguntando se quer reabrir esse arquivo em vez de rodar tudo de novo. Se o usuário preferir reabrir, mostre o conteúdo e pare aqui. Se preferir rodar de novo mesmo assim, siga pra etapa 3.
   - Se `updated` for diferente, siga pra etapa 3 normalmente (o cache está desatualizado).

3. **Fetch (raw)**
   - Use `ToolSearch` para localizar `getJiraIssue`. Se a chamada pedir autenticação, instrua o usuário a rodar `/mcp` e selecionar "claude.ai Atlassian Rovo".
   - Chame `getJiraIssue` com `cloudId`, `issueIdOrKey=<ISSUE-KEY>` e `fields` restrito a `["summary", "description", "comment", "status", "issuetype", "updated"]` — nunca peça o objeto completo, estoura o orçamento de contexto.
   - Crie o diretório de refinamento se não existir. Grave o retorno em `raw.json`.

4. **Contexto do Confluence (condicional)**
   - Procure links de página Confluence na `description` e nos `comment` de `raw.json` (URLs contendo `/wiki/` ou `atlassian.net/wiki`).
   - Se achar, use `ToolSearch` pra localizar `getConfluencePage` (ou `searchConfluenceUsingCql` se só tiver título/keyword, sem URL/ID direto) e busque o conteúdo relevante de cada página citada.
   - Grave um resumo do conteúdo relevante (com link de origem de cada página) em `confluence.md`. Se não achar nenhum link, pule a etapa sem criar o arquivo.
   - Se a chamada pedir autenticação separada, instrua o usuário a rodar `/mcp` de novo (mesmo conector Atlassian Rovo).

5. **Refinamento de negócio**
   - Invoque as skills `practices-business` e `practices-refinement` antes de escrever — elas apontam pra `knowledge/business.md` e `knowledge/refinement.md`, com o padrão de qualidade esperado (linguagem de negócio, ator explícito, critério de aceite testável, edge case explícito).
   - Leia `raw.json` (e `confluence.md`, se existir) e sintetize em `business.md`: contexto de negócio, regras, critérios de aceite, edge cases citados nos comentários/páginas — aplicando o padrão das skills invocadas acima.

6. **Clarify de negócio (condicional)**
   - Revise `business.md` procurando ambiguidade genuína (algo que a issue/comentários realmente deixam em aberto) — não invente pergunta por inventar.
   - Se achar lacuna, use `AskUserQuestion` e atualize `business.md` com a resposta antes de seguir. Se não achar nada, siga direto.

7. **Refinamento técnico (Serena)**
   - Invoque a skill `practices-code` antes de escrever — ela aponta pra `knowledge/{ddd,solid,clean-architecture,clean-code,design-patterns,database}.md` com o padrão técnico esperado (só aplique o que for pertinente ao escopo desta task, sem forçar checklist inteiro numa mudança pequena).
   - Resolva o repositório alvo: o `repoPath` vinculado, ou o repositório onde a sessão já está rodando.
   - Chame `mcp__serena__initial_instructions` e depois `mcp__serena__activate_project` nesse repositório (nunca no `TOOLS/`).
   - Use `find_symbol`, `find_referencing_symbols`, `get_symbols_overview` para mapear módulos/arquivos relacionados ao domínio descrito em `business.md`.
   - Escreva `technical.md` seguindo a estrutura de `knowledge/technical-refinement-template.md` (contexto, decisão recomendada, alternativas consideradas e por que foram descartadas, componentes impactados, diagrama se ajudar, riscos & mitigação, plano de rollout/reversibilidade, requisitos não-funcionais, dependências, alçada) — marque `N/A` nas seções que não se aplicam, sem omitir. Esse formato é o que torna o refinamento útil pro time, não só pra quem gerou.

8. **Clarify técnico (condicional)**
   - Só pergunte se, mesmo depois de listar as alternativas em `technical.md`, sobrar empate real entre 2+ abordagens ou uma dependência externa incerta que muda a decisão. Use `AskUserQuestion` e atualize `technical.md` com a resposta. Não repita perguntas já resolvidas na etapa de negócio.

9. **Consolidar**
   - Gere um uuid: `python3 -c "import uuid;print(uuid.uuid4())"`.
   - Escreva `final-<uuid>.md` com: cabeçalho (card key, link da issue via `webUrl`, timestamp), conteúdo de `business.md` e `technical.md`, e uma seção final **Checklist de implementação** — lista numerada de passos acionáveis (arquivos a mexer, ordem sugerida, o que validar), derivada de `technical.md` e pensada pra um agente pegar e executar direto, não só prosa.
   - Avise o usuário do caminho do arquivo final gerado.

## Notas

- Reaproveita `cloudId`/`boards.json` da skill `jira-sprint` — nunca duplicar essa lógica.
- Invocação de `practices-business`/`practices-refinement`/`practices-code` não substitui julgamento de escopo: task pequena não precisa do checklist inteiro de DDD/SOLID — aplique só o que for pertinente.
- Etapas 6 e 8 não são obrigatórias a cada rodada — só perguntam quando há lacuna/ambiguidade real, para não virar ruído.
- Etapa 4 (Confluence) e o arquivo `confluence.md` só existem quando há link relevante — não force busca sem pista nenhuma.
- Repetir a skill na mesma issue gera um novo `final-<uuid>.md` (histórico preservado) — não sobrescreve o anterior. `raw.json`/`business.md`/`technical.md`/`confluence.md` são sobrescritos a cada rodada (representam o estado mais recente do refinamento).
- Se `outputDir` apontar pra fora do `TOOLS/` (ex.: dentro do repo alvo), quem configurar é responsável por ignorar aquele diretório no `.gitignore` do repo alvo — esta skill não edita `.gitignore` de outros repositórios.
