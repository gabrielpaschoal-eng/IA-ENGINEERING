# Serena — setup

MCP de navegação/edição semântica de código via LSP, pra usar nos repositórios de trabalho reais plugados via `--add-dir` — não faz sentido pro `TOOLS/` em si (base pequena demais pra LSP compensar).

## Subir

```bash
cd settings/serena
cp .env.example .env    # ajuste SERENA_PROJECTS_DIR pro diretório pai dos seus repos
docker compose up -d
```

Roda via Docker, imagem oficial `ghcr.io/oraios/serena:latest` direto (sem Dockerfile próprio), transporte SSE na porta 9121 (dashboard web na 24282). `.env` e `config/` são locais/gitignored (cada pessoa tem seu próprio path e sua própria config/memórias).

Healthcheck no compose bate em `http://127.0.0.1:24282/dashboard/index.html` **de dentro do container** (o dashboard só escuta em loopback interno — não dá pra checar isso do host) — `docker compose ps` mostra `(healthy)`/`(unhealthy)` em vez de só "Up".

Se `docker compose up` der `permission denied` no socket do Docker (comum com o snap do Docker no Ubuntu, que não cria o grupo `docker` sozinho):

```bash
sudo addgroup --system docker
sudo adduser $USER docker
sudo snap disable docker && sudo snap enable docker
# depois: logout/login, ou `newgrp docker` / `sg docker -c "..."` pra testar sem relogar
```

## Registro no Claude Code

Automático via `.mcp.json` (raiz do repo, versionado — `url` é `http://localhost:${SERENA_PORT:-9121}/sse`, mesmo default do `docker-compose.yml`). Ninguém precisa rodar `claude mcp add` manualmente: ao abrir o harness, o Claude Code pede aprovação de confiança do servidor **uma vez por máquina** (`claude mcp list` mostra `⏸ Pending approval` até aceitar — some ao rodar `claude` de novo e aprovar o prompt). Requer o container do Serena já rodando (`docker compose up -d`) antes de aprovar/usar.

**Pegadinha do `${SERENA_PORT}`**: o Claude Code não lê `.env` sozinho pra expandir isso — só enxerga variável já exportada no shell antes de rodar `claude` (diferente do `docker compose`, que lê `settings/serena/.env` automático). Funciona sem nada extra enquanto a porta for a default (`9121`, igual nos dois lugares). Se customizar `SERENA_PORT` em `settings/serena/.env`, precisa também `export SERENA_PORT=<valor>` no shell antes de abrir a sessão, senão o `.mcp.json` cai no default enquanto o container sobe noutra porta.

`claude mcp reset-project-choices` reseta a aprovação (útil se o `.mcp.json` mudar e precisar reconfiar).

## Cobertura de linguagem

Das stacks que usamos (Go, TypeScript, Java, Python), a imagem oficial cobre TS e Java de cara (baixam o language server sozinhos na primeira ativação — npm / bundle com JRE embutido) e Python já funciona (`uv` já vem na imagem). **Go não funciona** nessa imagem — `gopls` exigiria toolchain Go pré-instalado, que a imagem oficial não tem; decidimos não manter um Dockerfile próprio pra isso (custo de manutenção > ganho), então navegação semântica em projeto Go fica sem suporte por enquanto.

## Memórias

Ao ativar um projeto pela primeira vez (`activate_project` / onboarding do Serena), ele grava memórias daquele repo em `.serena/memories/` dentro do próprio repo de trabalho (não dentro do `TOOLS/`).
