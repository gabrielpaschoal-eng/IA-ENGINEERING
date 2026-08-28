# Template de refinamento técnico

Estrutura pra `technical.md` (e a seção técnica do `final-<uuid>.md`) quando o refinamento é entregue pra outras pessoas do time decidirem/revisarem, não só pra uso pessoal imediato. Objetivo: qualquer engenheiro (ou outro arquiteto) lê o documento e entende o quê, por quê, o que foi descartado e qual o risco — sem precisar perguntar pra quem escreveu.

Seção sem conteúdo aplicável: marcar `N/A` com uma linha dizendo o motivo (não omitir a seção, não forçar conteúdo artificial).

```markdown
## Contexto/Problema

O que motiva essa mudança, em termos técnicos (liga com o `business.md`, mas aqui é o "porquê técnico").

## Decisão recomendada

A abordagem escolhida, em poucos parágrafos. Direto — não é a seção pra listar opção por opção (isso é a próxima).

## Alternativas consideradas

Pra cada alternativa descartada: o que era, por que não foi escolhida (trade-off concreto, não "achamos pior"). Se só existia uma abordagem razoável, diga isso explicitamente em vez de inventar alternativa fraca só pra preencher a seção.

## Componentes/módulos impactados

Lista de arquivos/módulos/serviços reais (path ou nome, não "algum lugar do código") — o que muda e o que só é lido/consultado.

## Diagrama

Mermaid (flowchart/sequência/C4 conforme o que ajudar a visualizar fluxo ou dependência entre componentes). Omitir com `N/A` se a mudança é simples o bastante pra não precisar.

## Riscos & mitigação

Risco concreto (não "pode dar problema") + o que mitiga cada um.

## Plano de rollout / reversibilidade

Como implantar com segurança (feature flag, migração em etapas, etc.) e como reverter se der errado. Ecoa `knowledge/database.md` (migração reversível) quando envolver schema.

## Requisitos não-funcionais

Performance, segurança, escala — só se for relevante pra essa mudança específica; `N/A` se não for.

## Dependências

Outro time, serviço externo, ou decisão que precisa estar resolvida antes.

## Alçada

A decisão pode seguir sozinha, ou precisa de review de outro arquiteto/tech lead antes de virar código? Se precisa, diga de quem.
```
