# Clean Architecture

Checklist prático — regra, sintoma de violação, direção do fix.

## Direção da dependência

- **Regra**: dependência sempre aponta pra dentro, em direção ao domínio — domínio não conhece aplicação, aplicação não conhece infraestrutura/framework/UI.
- **Sintoma**: entidade de domínio importando um tipo de framework web (`Request`/`Response`), ORM, ou SDK de infraestrutura.
- **Fix**: domínio expõe interfaces que a camada de fora implementa; nunca o inverso.

## Separação domínio / aplicação / infraestrutura

- **Regra**: domínio = regra de negócio pura; aplicação = orquestra casos de uso (chama domínio + portas); infraestrutura = implementação concreta de banco, fila, HTTP, etc.
- **Sintoma**: handler HTTP com regra de negócio inline, ou query SQL montada dentro do que deveria ser lógica de domínio.
- **Fix**: handler só traduz request → caso de uso → response; regra de negócio vive isolada, testável sem subir servidor/banco.

## Hexagonal / ports & adapters (opção, não dogma)

- **Regra**: quando fizer sentido isolar o domínio de múltiplas integrações externas (mais de uma fonte de dado, múltiplos consumidores), modelar como porta (interface no domínio/aplicação) + adaptador (implementação concreta por integração).
- **Sintoma de over-engineering**: criar porta+adaptador pra uma única implementação que nunca vai trocar, só "porque é boa prática" — isso é abstração sem 2º caso real.
- **Fix**: aplicar quando já existe (ou está claramente a caminho) mais de uma implementação real; caso contrário, chamada direta é mais simples e igualmente correta.

## Evitar módulo "deus"

- **Regra**: um módulo/pacote não deveria concentrar conhecimento de todo o sistema (todo mundo importa dele, ele importa de ninguém).
- **Sintoma**: pasta `utils`/`common`/`core` que cresce sem fronteira clara e vira dependência de tudo.
- **Fix**: dividir por domínio/feature; utilitário genuinamente genérico (sem regra de negócio) pode ficar central, regra de negócio não.

## Config fora do código

- **Regra**: o que muda por ambiente (URL, credencial, feature flag) é config, não constante hardcoded no código.
- **Sintoma**: valor de ambiente (produção vs. dev) espalhado como literal no meio da lógica.
- **Fix**: externalizar via variável de ambiente/arquivo de config, injetado — não editar código pra trocar de ambiente.
