# Refinamento de task

Checklist prático — regra, sintoma de violação, direção do fix.

## Critério de aceite testável

- **Regra**: todo critério de aceite deve dar pra responder objetivamente "passou ou não passou" — sem depender de opinião de quem lê.
- **Sintoma**: critério vago tipo "sistema deve responder rápido" ou "interface deve ser intuitiva" sem número/condição verificável.
- **Fix**: formato Given/When/Then (dado um contexto, quando uma ação ocorre, então um resultado observável acontece) ou checklist de condições explícitas.

## INVEST

- **Regra**: uma task bem refinada é Independente, Negociável, Valiosa (entrega valor perceptível), Estimável, Small (pequena o bastante pra caber num ciclo) e Testável.
- **Sintoma**: task que só faz sentido junto de outras 3 (não independente), ou grande demais pra estimar com confiança.
- **Fix**: quebrar em fatias menores que ainda entreguem valor sozinhas, ou explicitar a dependência entre tasks em vez de escondê-la.

## Banir verbo vago

- **Regra**: verbo de ação no refinamento vem com métrica ou condição concreta junto.
- **Sintoma**: "melhorar performance", "otimizar consulta", "deixar mais robusto" sem número, sem "de X para Y", sem condição de quando considerar resolvido.
- **Fix**: reescrever com número/condição (“reduzir tempo de resposta de 2s pra <500ms no p95”) ou, se ainda não dá pra medir, marcar como spike de investigação, não como task de entrega.

## Edge case explícito

- **Regra**: refinamento lista os casos de borda considerados (vazio, duplicado, concorrência, permissão negada, timeout) — não deixa implícito "trata os erros óbvios".
- **Sintoma**: refinamento só descreve o caminho feliz.
- **Fix**: adicionar seção de edge cases com o comportamento esperado de cada um, mesmo que a resposta seja "não tratado nesta versão" — desde que seja uma decisão explícita, não um esquecimento.

## Definition of ready

- **Regra**: task só entra em desenvolvimento com critério de aceite, escopo (o que está fora também) e dependência conhecida já resolvidos — não durante o desenvolvimento.
- **Sintoma**: começar a implementar e só então descobrir que falta decisão de negócio.
- **Fix**: se falta informação, isso é a lacuna que a etapa de clarify do refinamento deveria ter capturado antes de fechar o refinamento.
