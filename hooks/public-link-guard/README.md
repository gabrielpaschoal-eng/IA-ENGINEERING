# public-link-guard

Hook `PreToolUse` (matcher `ShareOnboardingGuide`) registrado em `.claude/settings.json`. Nega qualquer chamada a essa tool exceto `mode: "delete"`.

## Por quê

Incidente real: a skill publicou o `ONBOARDING.md` via `ShareOnboardingGuide` inferindo consentimento de um "pode fazer" que se referia a escrever o arquivo, não a publicá-lo. Regra geral do harness (ver `claude.md` — nunca publicar link público sem pedido explícito) virou hook técnico pra esse ponto específico.

## Comportamento (deliberadamente diferente dos outros guards)

- **Fail-safe fechado**: se `hooks/config/public-link-guard.json` estiver ausente/corrompido, o hook **bloqueia** (os outros guards deste harness fazem o oposto — ficam inativos se o config não carrega). Aqui o padrão seguro é bloquear, não liberar.
- `blockPublish: true` (default) bloqueia `check`/`create`/`update` — todo modo que gera ou atualiza um link público. `delete` sempre passa (remover exposição é sempre seguro).
- Não tem `exemptRepos` — é sobre a tool em si, não sobre um repositório alvo.

## Pra publicar de propósito

Confirme com o usuário que ele pediu essa publicação especificamente agora, depois edite `hooks/config/public-link-guard.json` pra `"blockPublish": false`, rode a publicação, e volte pra `true` — não deixe destravado por padrão.
