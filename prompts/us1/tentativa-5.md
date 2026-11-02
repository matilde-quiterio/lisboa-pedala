# US-1 — Quinta geração

## Contexto

A quinta geração foi feita sem novas alterações ao `ARCHITECTURE.md` ou aos ADRs.

Foi iniciada uma nova conversa e fornecidos apenas:

- `ARCHITECTURE.md`
- `ADR-002.md`
- `ADR-003.md`
- `ADR-004.md`

Foi usado o mesmo prompt das tentativas anteriores.

## Resultado da IA

A geração implementou:

- validação de utilizadores fictícios ativos;
- criação da viagem `PENDENTE` antes do destrancamento;
- persistência em SQLite;
- exclusividade de utilizador e bicicleta;
- distinção entre destrancamento e retirada física;
- identificação explícita da utilização nos eventos;
- processamento idempotente dos eventos;
- devolução recebida antes da retirada;
- tarifação com 45 minutos gratuitos e blocos de 15 minutos;
- cobrança simulada por cartão ou MB WAY;
- idempotência das cobranças;
- comunicação com uma doca simulada.

A geração incluiu também testes funcionais para alguns cenários da US-1.

## Testes funcionais da geração

Foram executados os testes incluídos pela própria geração.

Resultado:

```text
Ran 5 tests

OK
```

Foram testados:

- fluxo completo com cobrança;
- viagem de 45 minutos sem cobrança;
- repetição de um evento de retirada;
- devolução recebida antes da retirada;
- timeout no destrancamento mantendo a viagem `PENDENTE`.

Todos os testes fornecidos pela geração passaram.

## Fitness functions

Foi executado:

```powershell
python -m pytest tests/architecture -v
```

Resultado:

```text
test_allowed_to_use.py::test_allowed_to_use PASSED
test_no_cycles.py::test_no_circular_dependencies PASSED

2 passed
```

As fitness functions confirmaram que a geração respeita as dependências `allowed-to-use` e não introduz ciclos.

## Avaliação

A quinta geração é a mais completa até ao momento.

As ambiguidades identificadas nas gerações anteriores foram resolvidas e o código respeita as regras arquiteturais verificadas pelas fitness functions.

No entanto, o comportamento do prazo de retirada ainda não ficou totalmente implementado.

A geração permite processar a confirmação de que não houve retirada e que a bicicleta foi novamente bloqueada, mas não implementa de forma completa o controlo automático do prazo configurável seguido da tentativa de novo bloqueio pela doca simulada.

Esta regra já estava definida no `ARCHITECTURE.md` e no ADR-003, pelo que a limitação não resulta de uma ambiguidade da especificação.

## Decisão

A quinta geração é aceite do ponto de vista arquitetural e apresenta uma implementação funcional bastante completa da US-1.

No entanto, ainda não é considerada a versão final, devido à implementação incompleta do prazo de retirada e do novo bloqueio automático pela doca simulada.

Será feita uma nova geração sem alterar a arquitetura, para verificar se a regra já especificada é implementada corretamente.