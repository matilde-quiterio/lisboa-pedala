# Reflexão sobre a utilização da especificação e da IA

O desenvolvimento do Lisboa Pedala mostrou que ter uma especificação arquitetural detalhada ajuda bastante a orientar a geração de código com IA, mas não é suficiente, por si só, para garantir que o resultado está correto.

## O que a especificação não previu

As primeiras gerações expuseram alguns pontos que estavam implícitos na arquitetura, mas não suficientemente claros para uma ferramenta de geração.

Um exemplo foi a utilização de tipos internos entre componentes. A IA chegou a importar modelos de `Viagens` dentro de `Tarifação` e `Cobrança`, criando dependências que não estavam permitidas. Isto levou a clarificar que as regras `allowed-to-use` também se aplicam aos tipos utilizados nos contratos, e não apenas às chamadas entre serviços.

Também foi necessário tornar mais concretas algumas decisões do esqueleto funcional. A persistência passou a ser definida explicitamente com SQLite e foram clarificadas regras inicialmente demasiado abertas, como a autorização de utilizadores fictícios, o arredondamento dos blocos do tarifário e o comportamento do simulador de pagamentos.

Outro exemplo surgiu na comunicação entre `Telemetria` e `Manutenção`. A decisão de utilizar comunicação assíncrona através de um broker já existia, mas foi necessário garantir que as mensagens pendentes sobreviviam a uma reinicialização do processo. Por isso, a fila do broker passou a ser persistida.

Foi ainda necessário clarificar o tratamento de falhas após o fecho de uma viagem. Se a tarifação ou cobrança falharem, o evento físico de devolução já foi processado e não deve ser reutilizado. O retry passou a usar o estado persistido da viagem `TERMINADA`.

## Violações cometidas pela IA

A IA cometeu tanto violações estruturais como omissões de comportamento.

Na primeira geração do fluxo de viagens foram criadas as dependências proibidas:

```text id="pdqf3g"
Tarifação -> Viagens
Cobrança -> Viagens
```

Como `Viagens` já dependia de `Cobrança`, foi também criado o ciclo:

```text id="6y0sz7"
Cobrança -> Viagens -> Cobrança
```

Noutras gerações, as dependências estavam corretas, mas faltavam comportamentos importantes, como o controlo do prazo de retirada e o rebloqueio local da bicicleta.

Também foi necessário corrigir situações noutros fluxos, como garantir que mensagens repetidas de avaria não criavam ordens de manutenção duplicadas, que mensagens pendentes não se perdiam após reabrir o broker e que transições inválidas do ciclo de vida das ordens eram rejeitadas.

## O que as fitness functions detetaram

As fitness functions foram especialmente úteis na verificação de propriedades estruturais.

`test_allowed_to_use` detetou as dependências proibidas entre os componentes e `test_no_cycles` detetou o ciclo criado entre `Cobrança` e `Viagens`.

Isto permitiu rejeitar imediatamente código que violava as regras arquiteturais, antes de o considerar como uma implementação válida.

## O que passou despercebido

As fitness functions não conseguiram detetar vários problemas comportamentais.

Passaram sem erro situações como a ausência do controlo completo do prazo de retirada, o rebloqueio local da bicicleta, o retry correto após uma falha de tarifação ou cobrança, a persistência das mensagens do broker e algumas regras do ciclo de vida das ordens de manutenção.

Estes problemas só foram identificados através da revisão humana e de testes funcionais.

Por esse motivo, foram criados testes para validar situações como eventos fora de ordem, idempotência, falhas de destrancamento, retry da conclusão de uma viagem, persistência das mensagens do broker e transições inválidas de estado.

No final, a combinação de especificação, ADRs, fitness functions, testes funcionais e revisão humana revelou-se mais eficaz do que qualquer uma destas técnicas isoladamente. A geração com IA foi útil não apenas por produzir código, mas também porque os erros e omissões encontrados ajudaram a tornar progressivamente a arquitetura mais precisa.