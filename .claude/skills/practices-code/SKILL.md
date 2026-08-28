---
name: practices-code
description: Aplica padrões de qualidade de código (DDD, SOLID, Clean Architecture, Clean Code, Design Patterns, modelagem de banco) em revisão, design ou refinamento técnico. Use quando o usuário pedir explicitamente pra revisar/desenhar algo com um desses padrões nomeados ("revisa com SOLID", "isso segue DDD?", "essa modelagem de banco tá ok?", "que design pattern cabe aqui?"), ou quando for chamada internamente por outra skill (ex.: jira-refine) numa etapa de refinamento técnico. NÃO use pra fix pontual de poucas linhas, typo, ou mudança mecânica sem decisão de design envolvida.
---

# Practices — Código

Roteador de conhecimento técnico. O conteúdo fica em `knowledge/*.md` — esta skill decide qual arquivo ler, não repete o conteúdo aqui.

## Quando aplicar

- Revisão ou design de código onde exista uma decisão estrutural real (nova classe/módulo, novo domínio, escolha de abordagem, integração nova).
- Pedido cita um dos tópicos abaixo pelo nome.
- Invocação interna por outra skill (ex.: `jira-refine` na etapa de refinamento técnico).

## Quando não aplicar

- Fix de 1-3 linhas, typo, rename mecânico, ajuste de config sem decisão de design.
- Mudança que já segue um padrão existente no código — não reabrir debate de arquitetura pra repetir o que já está lá.

## Conhecimento disponível

| Tópico | Arquivo | Ler quando... |
|---|---|---|
| Domain-Driven Design | `knowledge/ddd.md` | mexer com modelo de domínio, entidade, regra de negócio no código |
| SOLID | `knowledge/solid.md` | pedido cita "SOLID" ou um dos 5 princípios, ou revisão de responsabilidade/acoplamento de classe |
| Clean Architecture | `knowledge/clean-architecture.md` | decisão de camada, direção de dependência, estrutura de módulo/pacote |
| Clean Code | `knowledge/clean-code.md` | nomeação, tamanho de função, duplicação, comentário |
| Design Patterns | `knowledge/design-patterns.md` | pedido cita um padrão nomeado, ou dúvida se vale a pena extrair uma abstração |
| Database | `knowledge/database.md` | modelagem de schema, transação, índice, migração |
| Template de refinamento técnico | `knowledge/technical-refinement-template.md` | escrevendo um documento de refinamento técnico pra outras pessoas do time lerem/decidirem (não uma resposta pontual de revisão) |

## Como usar

1. Se disparada standalone com um pedido específico ("revisa com SOLID"): leia só o arquivo do tópico citado.
2. Se disparada standalone com pedido amplo ("revisa esse código", "isso tá bem desenhado?") sem tópico específico: leia os arquivos relevantes pro que o código realmente faz (não leia os 6 por padrão — julgue pelo que está em jogo).
3. Se invocada internamente por outra skill (ex.: `jira-refine`, que já delimitou o escopo da task antes de chamar): leia todos os 6 arquivos de padrão e aplique o que for pertinente ao escopo já delimitado.
4. Aplique os checklists encontrados ao código/proposta em questão. Cite a regra específica violada (não só "viola SOLID" — diga qual princípio e por quê).
5. Se o resultado for um **documento** de refinamento técnico (não uma resposta de revisão inline), leia também `knowledge/technical-refinement-template.md` e siga a estrutura dele — marcando `N/A` nas seções que não se aplicam, sem omitir.

## Notas

- Não force aplicação de todos os tópicos numa mudança pequena — a régua geral do harness (não abstrair antes da hora, três linhas parecidas > abstração prematura) continua valendo por cima destes padrões.
- Os arquivos em `knowledge/` são compartilhados — outras skills também podem referenciá-los.
