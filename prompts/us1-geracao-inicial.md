# US-1 — Geração inicial

## Prompt enviado

Quero fazer a US-1 do Lisboa Pedala:
“Como assinante, desbloqueio e devolvo uma bicicleta e a viagem fica registada e cobrada.”
Vou mandar o `ARCHITECTURE.md` e os ADR-002, ADR-003 e ADR-004. Usa só esses ficheiros e não uses coisas de outras conversas.
O projeto é em Python.
Tenta seguir mesmo a arquitetura que está definida. Não cries componentes novos nem dependências que não estejam lá.
Primeiro diz-me que componentes vão estar envolvidos e como é que eles vão comunicar entre si. Depois faz o código necessário para esta US.
Se alguma parte necessária para implementar a US não estiver clara nos ficheiros, diz-me isso em vez de inventares uma decisão.

## Ficheiros de contexto fornecidos

- `ARCHITECTURE.md`
- `ADR-002.md`
- `ADR-003.md`
- `ADR-004.md`

## Resultado da IA

A IA identificou corretamente o fluxo principal da US-1 e os componentes envolvidos:

- Desbloqueio
- Utilizadores
- Viagens
- Comunicação das Docas
- Tarifação
- Cobrança
- Faturação

Também distinguiu corretamente a autorização do desbloqueio da retirada física da bicicleta e manteve a viagem no estado pendente até receber o evento de retirada.

No entanto, na geração dos contratos introduziu dependências que não estão permitidas no `ARCHITECTURE.md`.

### Violação 1 — Tarifação → Viagens

Foi gerado:

```python
if TYPE_CHECKING:
    from src.viagens.viagens.modelos import Viagem
```

Isto cria uma dependência de `Tarifação` para `Viagens`, que não está permitida nas regras `allowed-to-use`.

### Violação 2 — Cobrança → Viagens

Foi gerado:

```python
from src.viagens.viagens.modelos import DadosPagamento
```

Isto cria uma dependência de `Cobrança` para `Viagens`, que também não está permitida.

## Avaliação do resultado

O resultado foi parcialmente rejeitado.

A estrutura geral do fluxo estava de acordo com a arquitetura, mas o código não podia ser aceite diretamente porque introduziu dependências proibidas entre componentes.

As duas violações surgiram através da utilização de tipos definidos dentro do componente `Viagens`.

A IA também identificou alguns pontos que não estavam completamente definidos nos ficheiros fornecidos, como:

- tecnologia concreta de persistência;
- regras concretas de validação de utilizadores;
- fórmula concreta do tarifário;
- comportamento concreto do simulador de pagamentos;
- quando a faturação é aplicável.

Esses pontos não foram inventados pela IA, o que foi considerado positivo.

## Fitness functions

Depois de colocar no projeto o código gerado pela IA, foi executado:

```powershell
python -m pytest tests/architecture -v
```

Resultado:

```text
test_allowed_to_use.py::test_allowed_to_use FAILED
test_no_cycles.py::test_no_circular_dependencies FAILED
```

A fitness function `test_allowed_to_use` detetou duas dependências proibidas:

```text
Cobrança -> Viagens
Tarifação -> Viagens
```

Estas dependências foram introduzidas através de imports de tipos definidos dentro do componente `Viagens`.

A fitness function `test_no_cycles` detetou ainda o ciclo:

```text
Cobrança -> Viagens -> Cobrança
```

Este ciclo surgiu porque `Viagens` já depende de `Cobrança`, enquanto o código gerado fez `Cobrança` depender novamente de `Viagens`.

## Quem detetou as violações

As violações foram identificadas na revisão do código e confirmadas automaticamente pelas duas fitness functions arquiteturais.

## Decisão

O código gerado foi rejeitado nesta forma.

Será necessária uma nova geração ou correção dos contratos para que `Tarifação` e `Cobrança` deixem de depender de modelos internos de `Viagens` e a arquitetura volte a respeitar as regras `allowed-to-use` e a ausência de ciclos.