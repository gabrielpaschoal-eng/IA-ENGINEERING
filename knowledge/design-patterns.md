# Design Patterns

Checklist prático — quando usar, sintoma de mau uso, direção do fix. Padrão é resposta a um problema recorrente, não meta em si — o sintoma de mau uso mais comum é usar um padrão sem ter o problema que ele resolve.

## Strategy

- **Quando usar**: mais de uma forma de fazer a mesma coisa, escolhida em tempo de execução (ex.: formas diferentes de calcular frete/desconto).
- **Sintoma de mau uso**: criar `Strategy` pra uma única implementação que nunca varia — é indireção sem ganho.
- **Fix**: só extrair quando o 2º caso real aparece; até lá, função direta é mais simples.

## Factory

- **Quando usar**: construção de um objeto envolve decisão (qual subtipo, config condicional) que não deveria vazar pra quem só quer usar o objeto.
- **Sintoma de mau uso**: `Factory` que só chama `new X()` sem nenhuma decisão — construtor direto já resolveria.
- **Fix**: usar construtor direto até a construção de fato ganhar lógica condicional.

## Observer / eventos

- **Quando usar**: uma mudança de estado precisa notificar múltiplos interessados que não deveriam estar acoplados entre si (ver também domain event em `ddd.md`).
- **Sintoma de mau uso**: encadear listener→listener pra um fluxo simples de request/response que não precisa de desacoplamento nenhum.
- **Fix**: chamada direta quando só existe um consumidor conhecido; observer quando o número de consumidores é variável/desconhecido.

## Adapter

- **Quando usar**: integrar uma interface externa (SDK, API de terceiro) sem deixar o domínio depender do formato dela.
- **Sintoma de mau uso**: pular o adapter e espalhar o formato/tipo da lib externa direto pelas camadas de domínio/aplicação.
- **Fix**: um adapter na borda traduz pro tipo do domínio; o resto do sistema nunca vê o tipo externo.

## Regra geral de aplicação

- **Sintoma de over-engineering**: nomear a solução pelo padrão de design antes de ter certeza do problema (“vou usar Strategy aqui” antes de saber se realmente vai existir uma segunda variação).
- **Fix**: resolver o problema concreto primeiro; nomear/extrair o padrão quando a necessidade de flexibilizar aparecer de verdade — ecoa a regra do harness de não abstrair antes da hora.
