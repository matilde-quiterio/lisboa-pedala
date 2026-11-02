# US-1 — Quarta geração

## Contexto

Antes da quarta geração, o `ARCHITECTURE.md` foi clarificado para definir:

- que utilizadores fictícios existentes e ativos são autorizados;
- que qualquer bloco de 15 minutos iniciado após os 45 minutos gratuitos é cobrado por inteiro;
- o comportamento do simulador de pagamentos;
- a idempotência das cobranças.

## Resultado da IA

A quarta geração implementou corretamente:

- validação de utilizadores;
- tarifação após os 45 minutos gratuitos;
- cobrança simulada por cartão ou MB WAY;
- idempotência das cobranças;
- persistência em SQLite;
- exclusividade de utilizador e bicicleta;
- processamento idempotente dos eventos;
- tratamento de eventos fora de ordem;
- distinção entre destrancamento e retirada física.

A IA deixou de apresentar as três ambiguidades identificadas na geração anterior.

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

A quarta geração respeita a arquitetura e implementa os comportamentos funcionais que estavam em falta na tentativa anterior.

No entanto, não implementou completamente o comportamento da doca simulada relativo ao prazo de retirada.

O `ARCHITECTURE.md` e o ADR-003 já definem que:

- depois do destrancamento existe um prazo configurável para retirar a bicicleta;
- se esse prazo expirar sem retirada, a doca tenta voltar a bloquear a bicicleta;
- quando é confirmado que não ocorreu retirada e que a bicicleta ficou bloqueada, `Viagens` cancela a viagem `PENDENTE`.

Apesar desta regra já estar especificada, a geração não incluiu a implementação concreta deste comportamento.

Também foi definido o contrato de comunicação com a doca, mas não foi fornecida uma implementação completa da doca simulada que execute esse fluxo.

## Decisão

A quarta geração é aceite do ponto de vista arquitetural, uma vez que as fitness functions passaram.

A implementação ainda não é considerada totalmente completa de ponta a ponta devido à ausência do comportamento de timeout de retirada e novo bloqueio da doca simulada.

Esta limitação não resulta de ambiguidade da arquitetura, mas de uma regra já especificada que não foi implementada pela IA.