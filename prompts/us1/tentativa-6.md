# US-1 — Sexta geração

## Contexto

Depois da quinta geração, não foram feitas alterações ao `ARCHITECTURE.md` nem aos ADRs.

A nova geração foi feita numa conversa nova, usando apenas:

- `ARCHITECTURE.md`
- `ADR-002.md`
- `ADR-003.md`
- `ADR-004.md`

Nesta tentativa foi reforçado no prompt que todas as regras temporais e de falha da doca simulada deveriam ser implementadas de forma concreta.

## Prompt enviado

Quero fazer a US-1 do Lisboa Pedala:

“Como assinante, desbloqueio e devolvo uma bicicleta e a viagem fica registada e cobrada.”

Vou mandar o `ARCHITECTURE.md`, os ADR-002, ADR-003 e ADR-004.

Usa só esses ficheiros e não uses coisas de outras conversas.

O projeto é em Python.

Segue mesmo a arquitetura que está definida. Não cries componentes novos, não movas responsabilidades e não cries dependências que não estejam nas regras `allowed-to-use`.

Primeiro:

1. diz-me que componentes vão estar envolvidos;
2. explica resumidamente como comunicam entre si.

Depois faz o código necessário para esta US.

Implementa todas as regras necessárias ao fluxo da US-1 que estejam definidas no `ARCHITECTURE.md` e nos ADRs, incluindo os comportamentos temporais e de falha da doca simulada. Não deixes apenas contratos ou eventos sem a implementação concreta necessária para executar o fluxo de ponta a ponta.

Se alguma parte necessária para implementar a US não estiver clara no `ARCHITECTURE.md` ou nos ADRs, diz-me explicitamente qual é a ambiguidade em vez de inventares uma decisão.

## Resultado da IA

A sexta geração implementou:

- validação de utilizadores;
- criação da viagem `PENDENTE` antes do destrancamento;
- exclusividade de utilizador e bicicleta;
- persistência em SQLite;
- início da viagem apenas após retirada física;
- fim da viagem apenas após encaixe físico;
- timestamps físicos da doca;
- identificação dos eventos por `evento_id` e `utilizacao_id`;
- processamento idempotente;
- devolução recebida antes da retirada;
- falha confirmada de destrancamento;
- timeout mantendo a viagem `PENDENTE`;
- prazo configurável de retirada;
- rebloqueio local da bicicleta quando o prazo expira;
- funcionamento desse rebloqueio mesmo com a doca offline;
- armazenamento e reenvio de eventos;
- tarifação com 45 minutos gratuitos e blocos de 15 minutos;
- cobrança por cartão associado ou MB WAY;
- idempotência da cobrança;
- tarifa zero sem chamada à cobrança.

A IA não inventou valores concretos para preço do bloco, prazo de retirada, timeout ou utilizadores fictícios, utilizando configuração para esses valores.

Foi também identificada como não especificada a política a aplicar quando um evento permanece armazenado localmente durante mais de 24 horas.

## Testes funcionais

Foram integrados os testes funcionais da US-1 no projeto.

Foram testados:

- fluxo gratuito;
- tarifação e cobrança MB WAY;
- falha de destrancamento;
- timeout mantendo `PENDENTE`;
- prazo de retirada e rebloqueio local offline;
- devolução antes da retirada;
- idempotência de eventos.

## Fitness functions e testes funcionais

Foi executado:

```powershell
python -m pytest -v
```

Resultado:

```text
tests/architecture/test_allowed_to_use.py::test_allowed_to_use PASSED
tests/architecture/test_no_cycles.py::test_no_circular_dependencies PASSED
tests/us1/test_us1.py::test_fluxo_feliz_gratuito PASSED
tests/us1/test_us1.py::test_tarifa_blocos_e_cobranca_mbway PASSED
tests/us1/test_us1.py::test_falha_destrancamento_cancela_pendente PASSED
tests/us1/test_us1.py::test_timeout_mantem_pendente PASSED
tests/us1/test_us1.py::test_prazo_retirada_rebloqueia_localmente_mesmo_offline PASSED
tests/us1/test_us1.py::test_devolucao_antes_da_retirada_e_eventos_fisicos PASSED
tests/us1/test_us1.py::test_evento_repetido_nao_duplica_efeito PASSED

9 passed
```

## Avaliação

A sexta geração respeita as dependências `allowed-to-use`, não introduz ciclos e implementa de forma completa os principais comportamentos definidos para a US-1.

Ao contrário da tentativa anterior, o prazo de retirada e o rebloqueio local da doca simulada ficaram implementados e testados.

## Decisão

A sexta geração é aceite como implementação final da US-1.

As duas fitness functions arquiteturais e os sete testes funcionais passaram com sucesso.

Não serão realizadas novas gerações para esta user story.