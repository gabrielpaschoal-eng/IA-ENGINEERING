# DDD (Domain-Driven Design)

Checklist prático — regra, sintoma de violação, direção do fix.

## Ubiquitous language

- **Regra**: o nome usado no código (classe, método, variável) é o mesmo nome que o time de negócio usa pra falar da coisa.
- **Sintoma**: código fala `Record`/`Item`/`Data`/`Manager`/`Processor` genérico onde o negócio fala de um conceito específico (ex.: "Pedido", "Fatura", "Assinatura").
- **Fix**: renomear pro termo de negócio. Se o termo mudou, atualizar código e conversa junto — glossário não é documento à parte, é o próprio nome no código.

## Bounded context

- **Regra**: um mesmo termo pode significar coisas diferentes em partes diferentes do sistema (ex.: "Cliente" no módulo de vendas ≠ "Cliente" no módulo de cobrança) — cada contexto tem seu próprio modelo, não um modelo único "de verdade" pra tudo.
- **Sintoma**: uma entidade única tentando servir múltiplos módulos/times, acumulando campos que só fazem sentido em um dos usos.
- **Fix**: separar o modelo por contexto; tradução explícita (anti-corruption layer) na borda entre eles, não campo opcional acumulado.

## Entity vs value object

- **Regra**: entidade tem identidade e ciclo de vida (dois "Pedido #123" com os mesmos dados ainda são coisas diferentes); value object é definido só pelos valores que carrega (dois "Endereço" iguais são intercambiáveis, sem id).
- **Sintoma**: dar um `id` de banco pra tudo, inclusive coisas que deveriam ser comparadas por valor (dinheiro, intervalo de data, endereço).
- **Fix**: value objects imutáveis, comparados por igualdade estrutural, sem identidade própria.

## Aggregate / aggregate root

- **Regra**: um aggregate é o conjunto de objetos que precisa mudar junto de forma consistente; só a raiz do aggregate é acessada/modificada de fora — os demais objetos internos não têm referência externa direta.
- **Sintoma**: código externo navegando e alterando um objeto interno de outro aggregate diretamente (ex.: pegar um item de pedido e mudar o preço sem passar pelo pedido).
- **Fix**: toda alteração passa pela raiz; a raiz garante a invariante do conjunto inteiro.

## Domain event

- **Regra**: algo relevante que aconteceu no domínio (ex.: "PedidoConfirmado") vira um evento explícito, não só um `UPDATE` silencioso de status.
- **Sintoma**: lógica de reação a mudança de estado espalhada em vários lugares checando campo por campo (`if status == 'confirmed' && !wasNotified`).
- **Fix**: emitir o evento no ponto onde a mudança de fato acontece; quem precisa reagir, assina o evento.

## Domain model anêmico (evitar)

- **Regra**: entidade de domínio deve carregar comportamento, não só dados — regra de negócio pertence ao modelo, não a um "serviço" externo que só lê/escreve campos.
- **Sintoma**: classes de domínio só com getters/setters, e toda regra de negócio vive em `*Service`/`*Manager` que manipula esses campos de fora.
- **Fix**: mover a regra pra dentro da entidade/aggregate quando ela depende só do estado daquele objeto; serviço de aplicação orquestra, não decide regra de negócio sozinho.
