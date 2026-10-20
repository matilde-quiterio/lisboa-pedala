## 1. Particionamento de topo

Foi escolhido o particionamento **por domínio**, porque a decomposição anterior, feita através de workflows, já separou o sistema segundo responsabilidades de negócio, como Viagens, Manutenção, Faturação, Estações e Redistribuição.

Esta opção facilita a organização dos componentes por área funcional e torna mais simples perceber onde deve ficar cada responsabilidade. Como trade-off, exige maior atenção às dependências entre domínios e pode levar à repetição de alguns aspetos técnicos em diferentes áreas.

## 2. Vista de módulos

### Domínio de Operação de Viagens
- Desbloqueio
- Viagens
- Tarifação
- Cobrança
- Histórico de Viagens
- Faturação

### Domínio de Operação de Estações
- Comunicação das Docas
- Consulta de Estações
- Redistribuição

### Domínio de Manutenção da Frota
- Telemetria
- Manutenção

### Domínio de Reporting Municipal
- Relatórios Municipais

## 3. Regras allowed-to-use

As dependências dentro do mesmo domínio são permitidas.

As dependências entre domínios são restritas às seguintes relações:

- Operação de Viagens pode usar Operação de Estações.
- Operação de Estações pode usar Operação de Viagens.
- Reporting Municipal pode usar Operação de Viagens.
- Manutenção da Frota não depende dos restantes domínios.

Qualquer outra dependência entre domínios não é permitida.