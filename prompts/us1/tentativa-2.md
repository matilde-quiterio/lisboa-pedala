# US-1 — Segunda geração

## Contexto

Depois da primeira geração, foram clarificadas no `ARCHITECTURE.md`:

- as regras relativas a contratos e tipos partilhados entre componentes;
- a utilização de SQLite no esqueleto funcional;
- a necessidade de manter as operações de exclusividade e criação da viagem pendente na mesma transação.

## Resultado da IA

A segunda geração deixou de introduzir as dependências:

```text
Tarifação -> Viagens
Cobrança -> Viagens
```

Os contratos passaram a utilizar tipos simples nos parâmetros em vez de importar modelos internos do componente `Viagens`.

Também foi criada uma implementação SQLite para persistir o estado das viagens.

## Fitness functions

Foi executado:

```powershell
python -m pytest tests/architecture -v
```

Resultado:

```text
test_allowed_to_use.py::test_allowed_to_use PASSED
test_no_cycles.py::test_no_circular_dependencies PASSED
```

As duas fitness functions arquiteturais passaram.

## Avaliação

A segunda geração respeita as dependências `allowed-to-use` e não introduz dependências circulares.

As alterações feitas à especificação depois da primeira geração foram suficientes para evitar as violações arquiteturais anteriormente detetadas.

No entanto, a US-1 ainda não está completamente executável, porque os documentos fornecidos não definem concretamente:

- as regras de autorização de um utilizador;
- a fórmula do tarifário;
- a forma de selecionar a configuração municipal;
- o comportamento concreto do simulador de pagamento;
- quando a faturação é aplicável.

Essas decisões não foram inventadas pela IA.

## Decisão

A estrutura arquitetural da segunda geração é aceite.

Os comportamentos funcionais ainda não especificados devem ser definidos antes de considerar a US-1 completamente implementada e testável de ponta a ponta.