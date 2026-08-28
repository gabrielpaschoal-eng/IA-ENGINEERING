# Onboarding — TOOLS Harness

Bem-vindo(a) ao harness do time IA AUTOMATION. Este repositório (`TOOLS/`) é a base de onde o Claude Code roda no dia a dia — hooks, skills e configs que qualquer pessoa do time usa, plugados nos repositórios de trabalho reais.

Este guia é o "primeiro dia": deixa você operacional. Para referência completa e atualizada de cada peça, o índice é o [`claude.md`](claude.md) — ele aponta pro `README.md`/`SKILL.md` de cada hook/skill quando você precisar ir mais fundo.

## 1. Primeiro acesso

1. Clone este repositório.
2. Abra o Claude Code **a partir desta pasta** (`TOOLS/`) — é daqui que a sessão sempre roda:
   ```bash
   cd /caminho/para/TOOLS
   claude
   ```
   Outros repositórios (onde você realmente escreve código) entram na mesma sessão via `--add-dir` / `additionalDirectories` — você não sai do `TOOLS/`, só adiciona o repo de trabalho.
3. Os hooks já vêm registrados (`.claude/settings.json`) e carregam sozinhos. Não precisa configurar nada pra eles funcionarem.

## 2. O que já vem ativo, sem configurar nada

Dois guardrails rodam em toda sessão, silenciosamente, até você tentar algo que eles bloqueiam:

- **Guardrail de git**: bloqueia `git reset --hard`, `push --force`, `branch -D` e afins **sempre** (qualquer branch), a flag `--no-verify` sempre, e `commit`/`push` **na branch `main`/`master`** especificamente (funciona normal em qualquer outra branch). Se você levar um "comando bloqueado", é esperado — crie uma branch e siga. Detalhe: `hooks/git-branch-guard/README.md`.
- **Guardrail de escrita no Jira**: nenhuma skill deste harness consegue editar, comentar ou transicionar uma issue do Jira — é bloqueado a nível técnico, não só por instrução. Se seu fluxo de trabalho depende de automatizar isso, primeiro converse com o time — é uma decisão deliberada, não um bug.

Se algum desses te travar num caso legítimo, é ajuste de config (`hooks/config/*.json`), não de código — peça ajuda ou abra o arquivo e veja o padrão.

## 3. O que você ganha pra usar no dia a dia

### Jira

- **`jira-sprint`**: "quais cards estão na sprint do board X" — lista os issues da sprint atual. Primeiro uso pede pra você cadastrar seu(s) board(s) (fica salvo local, em `settings/jira/boards.json`, não é compartilhado via git).
- **`jira-refine`**: pega uma issue do Jira, gera um refinamento de negócio e um técnico (usando Serena pra mapear o código real do repo que você tá trabalhando), com pontos de pergunta quando falta informação. Fica em cache local — vira o ponto de partida pra você começar a desenvolver ou delegar a task pra um agente. Publicar o resultado como página no Confluence é opcional (a skill pergunta uma vez, por repositório).
- Ambas exigem o MCP **"claude.ai Atlassian Rovo"** autenticado na sessão — se pedir login, rode `/mcp` e selecione ele.

### Boas práticas de código

Pedir "revisa esse código com SOLID", "isso segue DDD?", "essa modelagem de banco tá ok?" aciona automaticamente uma das skills `practices-code` / `practices-refinement` / `practices-business`, que aplicam checklists práticos guardados em `knowledge/`. Elas também entram sozinhas durante o refinamento técnico do `jira-refine` — você não precisa chamar na mão.

### Serena (navegação de código via LSP)

Ferramentas de navegação/edição semântica (`find_symbol`, `find_referencing_symbols`, etc.) pros repositórios de trabalho reais — não pro `TOOLS/` em si. Precisa subir um container Docker uma vez por máquina:

```bash
cd settings/serena
cp .env.example .env    # ajuste SERENA_PROJECTS_DIR pro diretório pai dos seus repos
docker compose up -d
```

Na primeira vez que abrir o Claude Code com o container rodando, ele pede aprovação de confiança do servidor MCP — aceite o prompt. Setup completo e troubleshooting: `settings/serena/README.md`.

## 4. Se algo parecer quebrado

- Editou um hook ou `.claude/settings.json` no meio da sessão? Rode `/hooks` uma vez (ou reinicie a sessão) pra recarregar.
- MCP pedindo aprovação de novo depois que você já aceitou? `claude mcp list` mostra o status; `/mcp` recarrega registros de escopo não-project.
- Guardrail bloqueando algo que você tem certeza que devia passar? Não contorne no improviso — ajuste o JSON de config correspondente (`hooks/config/`) ou converse com quem mantém o harness.

## 5. Contribuindo de volta

Tudo que for criado para o harness (hook, script, config, skill) fica dentro do `TOOLS/` — nunca em `~/.claude/` pessoal. Ao adicionar ou mudar algo, mantenha o `claude.md` como índice atualizado (ele deve ficar enxuto — detalhe pesado vai pro `README.md`/`SKILL.md` do próprio hook/skill, não pro índice).
