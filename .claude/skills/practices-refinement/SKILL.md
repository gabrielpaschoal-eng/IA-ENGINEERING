---
name: practices-refinement
description: Aplica boas práticas de refinamento de task (critério de aceite testável, INVEST, edge cases, definition of ready) ao escrever ou revisar uma história/task. Use quando o usuário pedir pra escrever ou revisar critério de aceite, refinar uma história, ou quando for chamada internamente por outra skill (ex.: jira-refine) numa etapa de refinamento. NÃO use pra tarefa técnica pontual sem nenhuma história/critério de aceite envolvido.
---

# Practices — Refinamento

Roteador de conhecimento sobre refinamento de task. O conteúdo fica em `knowledge/refinement.md` — esta skill decide quando aplicar, não repete o conteúdo aqui.

## Quando aplicar

- Escrever ou revisar critério de aceite, história de usuário, ou task antes de entrar em desenvolvimento.
- Invocação interna por outra skill (ex.: `jira-refine` na etapa de refinamento de negócio).

## Quando não aplicar

- Tarefa técnica isolada (ex.: "atualiza essa dependência") sem critério de aceite/história por trás.

## Como usar

1. Leia `knowledge/refinement.md`.
2. Revise o conteúdo em questão contra cada critério (aceite testável, INVEST, sem verbo vago, edge case explícito, definition of ready).
3. Aponte especificamente onde falha (não "está vago" — diga qual verbo/frase é vago e sugira a reescrita com métrica/condição).

## Notas

- Complementar a `practices-business` (que cobre a linguagem/modelagem de negócio) — esta skill foca no formato e testabilidade do refinamento, não no conteúdo de domínio em si.
