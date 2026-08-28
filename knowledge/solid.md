# SOLID

Checklist prático — regra, sintoma de violação, direção do fix.

## SRP — Single Responsibility

- **Regra**: uma classe/módulo tem um único motivo pra mudar.
- **Sintoma**: classe com nome genérico (`Manager`, `Helper`, `Utils`) que mistura validação + persistência + notificação + formatação num só lugar.
- **Fix**: separar por motivo de mudança — se validação muda por regra de negócio e persistência muda por troca de banco, são responsabilidades diferentes, viram classes diferentes.

## OCP — Open/Closed

- **Regra**: aberto pra extensão, fechado pra modificação — adicionar comportamento novo não deveria exigir editar código já testado e funcionando.
- **Sintoma**: `if/switch` gigante por tipo (`if type == "A" ... else if type == "B" ...`) que cresce toda vez que aparece um tipo novo.
- **Fix**: polimorfismo/strategy — cada tipo implementa sua própria variação, o código que orquestra não muda quando um tipo novo entra.
- **Cuidado**: não aplicar preventivamente pra um único caso hoje — abstração sem 2º caso real é over-engineering, não OCP.

## LSP — Liskov Substitution

- **Regra**: uma subclasse tem que poder substituir a classe-mãe sem quebrar o comportamento esperado por quem usa a classe-mãe.
- **Sintoma**: subclasse que lança exceção "não suportado" num método que a classe-mãe implementa normalmente, ou que muda o contrato (pré/pós-condição) de forma incompatível.
- **Fix**: se o subtipo não consegue cumprir o contrato da mãe, não é uma subclasse dela — repensar a hierarquia (composição em vez de herança, ou hierarquia diferente).

## ISP — Interface Segregation

- **Regra**: interface pequena e específica pro que o cliente realmente usa, em vez de uma interface "canivete suíço".
- **Sintoma**: implementação obrigada a criar método vazio/`throw NotImplementedException` porque a interface exige algo que aquele caso não usa.
- **Fix**: quebrar a interface grande em interfaces menores e coesas; cada cliente depende só do que consome.

## DIP — Dependency Inversion

- **Regra**: módulo de alto nível (regra de negócio) não depende de módulo de baixo nível (banco, HTTP, fila) — os dois dependem de uma abstração; a direção da dependência aponta pra dentro do domínio.
- **Sintoma**: regra de negócio importando diretamente um cliente de banco/SDK externo específico, difícil de testar sem infraestrutura real de pé.
- **Fix**: domínio define a interface (porta) que precisa; infraestrutura implementa essa interface (adaptador) e é injetada — não o contrário.
