# Clean Code

Checklist prático — regra, sintoma de violação, direção do fix.

## Nomeação

- **Regra**: nome diz o quê/por quê, sem precisar abrir a implementação. Nome específico > nome genérico.
- **Sintoma**: `data`, `temp`, `flag`, `handleStuff`, `processIt` — nome que não distingue essa coisa de qualquer outra coisa no sistema.
- **Fix**: renomear pro que a coisa realmente representa/faz, no vocabulário do domínio.

## Funções pequenas e coesas

- **Regra**: uma função faz uma coisa, no nível de abstração que o nome promete.
- **Sintoma**: função com múltiplos níveis de abstração misturados (validação de baixo nível + orquestração de alto nível no mesmo bloco), ou que exige rolar a tela pra ler inteira.
- **Fix**: extrair sub-passos em funções nomeadas; a função principal vira uma lista legível de chamadas.

## Evitar duplicação

- **Regra**: mesma lógica repetida em 2+ lugares é uma fonte de bug (corrige um, esquece o outro).
- **Sintoma**: bloco de código quase idêntico colado em vários arquivos/funções.
- **Fix**: extrair pra uma função/módulo compartilhado — mas só quando a duplicação é de fato a mesma regra, não coincidência estrutural (duas coisas parecidas por acaso não precisam virar uma abstração só).

## Comentário só quando não-óbvio

- **Regra**: comentário explica o porquê não-óbvio (uma decisão, uma restrição, um workaround) — não o quê (isso o código já diz, se bem nomeado).
- **Sintoma**: comentário repetindo o nome da função/variável em português, ou bloco de docstring longo pra função trivial.
- **Fix**: remover comentário que só parafraseia o código; manter só o que explicaria uma decisão que confundiria quem lê depois.

## Tratamento de erro

- **Regra**: validar só na borda do sistema (input do usuário, resposta de API externa); dentro do sistema, confiar nas garantias internas.
- **Sintoma**: `if x == null` repetido em toda função que recebe `x`, mesmo quando `x` já foi validado mais cedo no mesmo fluxo.
- **Fix**: validar uma vez na entrada; código interno assume o dado válido.
