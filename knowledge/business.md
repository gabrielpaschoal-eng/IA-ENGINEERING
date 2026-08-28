# Refinamento de negócio

Checklist prático — regra, sintoma de violação, direção do fix.

## Linguagem de negócio, não jargão técnico

- **Regra**: refinamento de negócio descreve o problema/regra na linguagem de quem pediu (stakeholder), não em termo de implementação (tabela, endpoint, classe).
- **Sintoma**: refinamento de negócio já citando nome de tabela/campo/endpoint como se fosse a própria regra.
- **Fix**: descrever a regra em termos que o stakeholder reconheceria; detalhe de implementação fica pro refinamento técnico.

## Atores/personas explícitos

- **Regra**: toda regra de negócio deixa claro quem faz o quê (que papel/ator dispara a ação, quem é afetado).
- **Sintoma**: regra escrita na voz passiva sem sujeito ("o pedido é cancelado quando...") sem dizer quem cancela e por quê.
- **Fix**: nomear o ator (cliente, operador, sistema externo) em cada regra.

## Separar regra de negócio de detalhe de implementação

- **Regra**: regra de negócio é o "o quê"/"por quê" (o que precisa ser verdade pro negócio funcionar); implementação é o "como" (qual componente faz isso).
- **Sintoma**: refinamento de negócio já decidindo abordagem técnica ("vamos usar fila pra processar isso") antes de sequer descrever a regra que motiva.
- **Fix**: mover decisão de "como" pro refinamento técnico; negócio registra só a regra e a motivação.

## Métrica de sucesso

- **Regra**: toda mudança de negócio relevante tem um jeito de saber se funcionou (métrica, comportamento observável).
- **Sintoma**: pedido de negócio sem nenhuma forma de validar se o resultado esperado de fato aconteceu.
- **Fix**: adicionar métrica ou sinal observável (mesmo que qualitativo) de sucesso.

## Escopo fora explícito

- **Regra**: refinamento de negócio diz explicitamente o que **não** está incluído, quando há ambiguidade real de fronteira.
- **Sintoma**: descrição só do que entra, deixando pra descobrir depois (em desenvolvimento) o que ficou de fora.
- **Fix**: listar exclusões conhecidas junto do escopo — mesma lógica do "definition of ready" em `refinement.md`.
