# Database

Checklist prático — regra, sintoma de violação, direção do fix.

## Modelagem (normalização vs. desnormalização consciente)

- **Regra**: normalizar por padrão (sem dado duplicado, uma fonte de verdade por fato); desnormalizar só com motivo explícito e medido (performance de leitura comprovadamente necessária).
- **Sintoma**: mesmo dado (ex.: nome de cliente) copiado em várias tabelas "pra evitar join", sem medir se o join era de fato um problema.
- **Fix**: normalizar primeiro; desnormalizar depois, documentando o motivo e como manter os dados duplicados consistentes.

## Transação e consistência

- **Regra**: operação que precisa ser tudo-ou-nada (ex.: debitar de uma conta e creditar em outra) fica dentro de uma transação — nunca duas escritas separadas "torcendo" pra segunda não falhar.
- **Sintoma**: múltiplas escritas relacionadas em chamadas separadas, sem transação nem compensação em caso de falha no meio do caminho.
- **Fix**: agrupar em transação; se atravessa serviços/bancos diferentes (sem transação distribuída disponível), desenhar compensação explícita (saga) em vez de assumir que nunca falha no meio.

## Índice

- **Regra**: índice existe pra sustentar um padrão de consulta real (`WHERE`/`JOIN`/`ORDER BY` frequente) — não é "quanto mais índice melhor" (cada índice custa escrita mais lenta e espaço).
- **Sintoma**: tabela sem índice nas colunas usadas em filtro frequente, ou o oposto — índice em coluna que nunca é usada em filtro/ordenação.
- **Fix**: índice guiado pelo padrão de acesso real (query plan), não por suposição.

## Migração reversível

- **Regra**: toda migração de schema tem um caminho de volta conhecido antes de rodar em produção — mesma régua de reversibilidade já usada nos guardrails deste harness (preferir passo reversível a `DROP`/mudança destrutiva sem plano).
- **Sintoma**: migração que remove coluna/tabela sem backup ou sem etapa intermediária (deprecar → confirmar não uso → remover).
- **Fix**: migração destrutiva em etapas (parar de escrever → confirmar leitura zero → só então remover), nunca num passo só.
