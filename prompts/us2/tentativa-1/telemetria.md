# US-2 — Geração inicial: Telemetria

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

### Violação 1 — Comunicação síncrona

O método `publicar()` do broker executava imediatamente os callbacks subscritos. Assim, Telemetria esperava que Manutenção processasse a mensagem, contrariando a comunicação assíncrona definida no ADR-005.

Detetada durante uma revisão assistida por ChatGPT. As fitness functions existentes não verificaram este comportamento.

### Violação 2 — Mensagens não persistidas

O broker mantinha os subscritores em memória, mas não persistia as mensagens nem as confirmava após o processamento, contrariando o ADR-005.

Detetada durante uma revisão assistida por ChatGPT. As fitness functions existentes não verificaram este comportamento.

### Violação 3 — Estado da bicicleta não atualizado

O componente recebia telemetria e publicava uma mensagem quando havia avaria, mas não atualizava o estado da bicicleta, como definido no workflow do documento 02.

Detetada durante uma revisão assistida por ChatGPT. As fitness functions existentes não verificaram este comportamento.

## Decisão

Telemetria foi rejeitado nesta versão e não foi integrado. O broker e o tratamento da telemetria precisam de ser corrigidos antes da integração.