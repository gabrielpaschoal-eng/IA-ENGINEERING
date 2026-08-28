---
name: practices-business
description: Aplica boas práticas de modelagem/refinamento de negócio (linguagem de stakeholder, atores explícitos, métrica de sucesso, escopo fora) ao escrever ou revisar uma especificação funcional ou regra de negócio. Use quando o usuário pedir pra modelar/revisar regra de negócio, especificação funcional, ou quando for chamada internamente por outra skill (ex.: jira-refine) numa etapa de refinamento de negócio. NÃO use pra decisão puramente técnica sem regra de negócio envolvida.
---

# Practices — Negócio

Roteador de conhecimento sobre modelagem de negócio. O conteúdo fica em `knowledge/business.md` — esta skill decide quando aplicar, não repete o conteúdo aqui.

## Quando aplicar

- Escrever ou revisar regra de negócio, especificação funcional, ou o lado "o quê/por quê" de uma task.
- Invocação interna por outra skill (ex.: `jira-refine` na etapa de refinamento de negócio).

## Quando não aplicar

- Decisão puramente técnica (escolha de biblioteca, estrutura de dado interna) sem regra de negócio por trás.

## Como usar

1. Leia `knowledge/business.md`.
2. Revise o conteúdo em questão contra cada critério (linguagem de negócio, ator explícito, regra separada de implementação, métrica de sucesso, escopo fora).
3. Aponte especificamente onde falha (ex.: "essa frase já descreve implementação, não regra — mover pro refinamento técnico").

## Notas

- Complementar a `practices-refinement` (que cobre formato/testabilidade do critério de aceite) — esta skill foca no conteúdo de domínio/negócio em si.
