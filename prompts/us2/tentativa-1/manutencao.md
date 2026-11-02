# US-2 — Geração inicial: Manutenção

## Pedido

Quero implementar a US-2: como técnico, recebo uma ordem de manutenção quando uma bicicleta reporta uma avaria.

Gera os componentes Telemetria e Manutenção em Python 3.11+, respeitando o ARCHITECTURE.md, os ADR-004 e ADR-005 e o 02-componentes.md.

Usa a estrutura existente:
- src/manutencao/telemetria.py
- src/manutencao/manutencao.py
- tests/architecture/ para os testes de arquitetura existentes

Usa SQLite para persistir os dados entre execuções. Coloca os testes funcionais da US-2 em tests/test_us2_manutencao.py e cria uma CLI para demonstrar o fluxo.

A comunicação Telemetria → Manutenção deve respeitar o ADR-005. Inclui testes para o processamento de uma avaria e para o reenvio da mesma mensagem sem duplicar a ordem. Indica os ficheiros criados ou alterados e como executar a CLI e os testes.

## Ficheiros de contexto fornecidos

- `ARCHITECTURE.md`
- `ADR-004.md`
- `ADR-005.md`
- `02-componentes.md`

O pedido também indicava a estrutura existente dos componentes e dos testes de arquitetura.

## Resultado da IA

Resultado: rejeitado para integração.

### Violação 1 — Dependência proibida Manutenção → Telemetria

Manutenção importava `Broker` e `MensagemAvaria` de Telemetria, criando a dependência proibida Manutenção → Telemetria.

A dependência foi identificada numa revisão assistida por ChatGPT e confirmada pela fitness function `test_allowed_to_use`.

### Fitness functions

Foi executado:

```powershell
python -m pytest tests/architecture/ -v
```

Resultado:

```text
test_allowed_to_use: FAILED — detetou Manutenção → Telemetria
test_no_circular_dependencies: PASSED
```

A dependência não criou um ciclo, por isso o teste de ciclos passou.

### Fragilidades identificadas na revisão

O processamento consultava se já existia uma ordem para a mensagem antes de a inserir. Duas entregas simultâneas poderiam passar essa consulta; a restrição `UNIQUE` impediria duplicar a linha, mas poderia causar uma exceção não tratada.

O fecho da ordem também permitia concluir sem descrição da intervenção e voltar a alterar uma ordem já concluída ou cancelada.

Estes pontos foram identificados na revisão assistida por ChatGPT. As fitness functions existentes não os verificaram.

## Testes funcionais gerados

Os testes assumiam que `publicar()` criava imediatamente a ordem. Reproduziam, assim, o comportamento síncrono do broker em vez de verificar a publicação e o consumo assíncronos definidos no ADR-005.

O teste de reenvio verificava que a mesma mensagem não criava uma segunda ordem, mas não verificava a persistência da mensagem nem a reentrega após uma falha.

O teste de reporte manual verificava os dados devolvidos pelo serviço, mas não voltava a consultar a ordem na base de dados para confirmar a persistência.

O resultado da execução dos testes funcionais não foi registado. As fitness functions existentes não verificam o comportamento desses testes.

## CLI

A `main.py` foi gerada para demonstrar a US-2, mas dependia do callback síncrono do broker para criar imediatamente a ordem. Deve ser revista para demonstrar a publicação e o consumo da mensagem em passos separados.

Quando já existem ordens guardadas, a CLI limita-se a listá-las, sem demonstrar novamente o fluxo completo. Isto foi identificado na revisão; não é verificado pelas fitness functions de arquitetura.

## Decisão

Manutenção foi rejeitado nesta versão e não foi integrado. Devem ser corrigidas a dependência proibida e as fragilidades identificadas. Os testes funcionais e a CLI também devem ser ajustados ao fluxo assíncrono definido no ADR-005.