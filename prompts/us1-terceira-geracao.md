# US-1 — Terceira geração

## Contexto

Depois da segunda geração, foram clarificados no `ARCHITECTURE.md` e no ADR-003:

- a distinção entre destrancamento e retirada física;
- a criação da viagem `PENDENTE` antes do comando à doca;
- a utilização de um identificador comum da utilização nos eventos;
- o processamento idempotente de eventos;
- o tratamento de eventos atrasados ou fora de ordem;
- a exclusão de Faturação do fluxo obrigatório da US-1.

O ADR-002 foi também corrigido para indicar que a viagem só se inicia após a retirada física da bicicleta.

## Resultado da IA

A terceira geração identificou corretamente os componentes da US-1:

- Utilizadores
- Desbloqueio
- Viagens
- Comunicação das Docas
- Tarifação
- Cobrança

A IA respeitou as dependências `allowed-to-use` e passou a utilizar o identificador da utilização nos eventos de retirada e devolução.

Foram também tratados:

- persistência em SQLite;
- exclusividade de utilizador e bicicleta;
- eventos repetidos;
- devoluções recebidas antes da retirada;
- proteção dos instantes físicos já confirmados;
- separação entre fecho da viagem, tarifação e cobrança.

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

As fitness functions confirmaram que a geração respeita as dependências permitidas e não introduz ciclos.

## Avaliação

A terceira geração corrigiu os problemas arquiteturais encontrados nas tentativas anteriores.

No entanto, a US-1 ainda não ficou completamente executável porque a IA identificou três comportamentos que continuavam por definir:

- critério concreto de autorização dos utilizadores fictícios;
- tratamento de frações dos blocos de 15 minutos;
- regra de sucesso ou falha do pagamento simulado.

Esses comportamentos não foram inventados pela IA.

## Decisão

A estrutura arquitetural da terceira geração é aceite.

Antes da geração seguinte, o `ARCHITECTURE.md` foi clarificado para definir:

- que utilizadores fictícios existentes e ativos são autorizados;
- que qualquer bloco de 15 minutos iniciado após os 45 minutos gratuitos é cobrado por inteiro;
- que a cobrança simulada é aceite quando existem os dados necessários ao meio de pagamento escolhido;
- que a mesma chave de idempotência não pode originar mais do que uma cobrança.