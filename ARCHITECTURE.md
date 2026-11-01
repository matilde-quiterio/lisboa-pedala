# ARCHITECTURE — Lisboa Pedala

Este ficheiro define as regras arquiteturais que devem ser respeitadas por qualquer implementação ou código gerado por IA. As decisões detalhadas encontram-se em `docs/` e nos ADRs em `docs/adr/`.

## 1. Componentes

A arquitetura lógica é particionada por domínio. Cada componente tem uma responsabilidade única e vive no namespace indicado.

| Componente | Responsabilidade | Namespace |
|---|---|---|
| Utilizadores | Gerir identificação e dados da conta necessários ao acesso e tarifação. | `src.viagens.utilizadores` |
| Desbloqueio | Validar e executar o desbloqueio de uma bicicleta. | `src.viagens.desbloqueio` |
| Viagens | Registar e manter o estado das viagens e coordenar a sua conclusão. | `src.viagens.viagens` |
| Tarifação | Calcular a tarifa aplicável a uma viagem. | `src.viagens.tarifacao` |
| Cobrança | Processar a cobrança ao utilizador. | `src.viagens.cobranca` |
| Histórico de Viagens | Disponibilizar ao utilizador as viagens realizadas. | `src.viagens.historico` |
| Faturação | Gerar, guardar e disponibilizar faturas associadas às viagens. | `src.viagens.faturacao` |
| Comunicação das Docas | Enviar comandos e receber eventos das docas, encaminhando-os para os componentes responsáveis. | `src.estacoes.comunicacao_docas` |
| Consulta de Estações | Disponibilizar bicicletas disponíveis e docas livres por estação. | `src.estacoes.consulta_estacoes` |
| Planeamento de Redistribuição | Determinar as quantidades de bicicletas a recolher e entregar em cada estação. | `src.redistribuicao.planeamento_redistribuicao` |
| Planeamento de Rotas | Calcular e disponibilizar as rotas das equipas de redistribuição. | `src.redistribuicao.planeamento_rotas` |
| Telemetria | Receber e processar os dados enviados pelas bicicletas elétricas. | `src.manutencao.telemetria` |
| Manutenção | Gerir reportes de avaria, ordens de manutenção e intervenções. | `src.manutencao.manutencao` |
| Relatórios Municipais | Consultar e agregar dados para produzir o relatório mensal municipal. | `src.reporting.relatorios_municipais` |

## 2. Regras allowed-to-use

Apenas são permitidas as seguintes dependências entre componentes:

```text
desbloqueio -> utilizadores
desbloqueio -> comunicacao_docas

comunicacao_docas -> viagens
comunicacao_docas -> consulta_estacoes

viagens -> tarifacao
viagens -> cobranca

tarifacao -> utilizadores
cobranca -> utilizadores

historico -> viagens

faturacao -> viagens
faturacao -> cobranca

planeamento_redistribuicao -> consulta_estacoes
planeamento_redistribuicao -> planeamento_rotas

telemetria -> manutencao
```

`relatorios_municipais` não depende de outros componentes e pode consultar diretamente a base de dados partilhada apenas em leitura.

**Qualquer dependência entre componentes não listada acima é proibida.**

Em particular:

- `desbloqueio` não pode depender diretamente de `viagens`;
- `tarifacao` não pode depender de `cobranca`;
- `relatorios_municipais` não pode depender de `viagens`;
- os restantes componentes não podem depender de `relatorios_municipais`.

O mecanismo de comunicação não altera estas regras de dependência lógica.

## 3. Características arquiteturais prioritárias

### Availability

O serviço de desbloqueio deve manter elevada disponibilidade, dado existir penalização quando mais de 10% das estações não conseguem realizar desbloqueios.

Implicações para o código:

- o backend principal deve poder executar em múltiplas instâncias equivalentes;
- o código do backend não deve depender de estado local em memória necessário ao funcionamento de pedidos posteriores;
- operações suscetíveis de repetição devem evitar efeitos duplicados;
- a implementação deve assumir que uma instância pode falhar e outra continuar a servir pedidos.

Novos desbloqueios continuam a exigir comunicação e autorização do backend, conforme ADR-003.

### Robustness

O sistema deve tolerar falhas temporárias de comunicação e reenvio de mensagens ou eventos.

Implicações para o código:

- eventos reenviados pelas docas devem ser processados de forma idempotente;
- o mesmo evento não pode iniciar ou fechar a mesma viagem mais do que uma vez;
- uma devolução recebida após recuperação da ligação deve usar como hora de fim o instante de encaixe registado pela doca;
- mensagens de avaria reenviadas pelo broker não podem criar ordens de manutenção duplicadas;
- falhas de comunicação devem ser tratadas explicitamente e não assumidas como impossíveis.

### Configurability

A plataforma deve suportar tarifários próprios de diferentes municípios sem alterar a lógica central.

Implicações para o código:

- tarifários e valores específicos de um município não podem estar hardcoded;
- `tarifacao` deve receber ou obter a configuração aplicável ao município;
- a alteração de um tarifário não deve exigir alterações nos restantes componentes.

## 4. Acoplamento temporal e unidades de trabalho

O fluxo principal deve respeitar esta ordem:

```text
validar utilizador
-> solicitar desbloqueio
-> confirmar desbloqueio físico
-> iniciar viagem
-> confirmar encaixe na doca
-> fechar viagem
-> calcular tarifa
-> cobrar, se aplicável
```

Regras obrigatórias:

1. Uma viagem só pode ser iniciada depois da confirmação física do desbloqueio.
2. Uma viagem só pode ser fechada depois da confirmação de encaixe da bicicleta.
3. A tarifa só pode ser calculada depois de a viagem estar fechada.
4. A cobrança só pode ocorrer depois de a tarifa ter sido calculada.
5. Se a tarifa for zero, não é efetuada cobrança.
6. O processamento repetido do mesmo evento não pode duplicar uma viagem nem uma cobrança.

Dentro de `Viagens`, a alteração do estado da viagem e a persistência desse novo estado devem fazer parte da mesma unidade de trabalho.

O fecho da viagem, o cálculo da tarifa e a cobrança respeitam uma ordem temporal, mas **não constituem uma única transação distribuída**.

No fluxo `Telemetria -> Manutenção`, a comunicação é assíncrona: Telemetria publica a mensagem no broker e não espera pela criação da ordem de manutenção.

## 5. Convenções de código

- O código é organizado primeiro por domínio: `viagens`, `estacoes`, `redistribuicao`, `manutencao` e `reporting`.
- Cada componente deve manter apenas a responsabilidade definida na secção 1.
- Dependências entre componentes devem respeitar estritamente a secção 2.
- A comunicação entre componentes deve ser feita através de contratos explícitos.
- O fluxo `desbloquear -> devolver -> cobrar` utiliza comunicação síncrona.
- `Telemetria -> Manutenção` utiliza comunicação assíncrona através do broker.
- A lógica de tarifação pertence exclusivamente a `tarifacao`.
- A coordenação entre fecho da viagem, tarifação e cobrança pertence a `viagens`.
- A comunicação física com as docas pertence a `comunicacao_docas`.
- Reporting apenas pode escrever o seu próprio resultado; o acesso aos dados operacionais é read-only.
- Código para tratamento de reenvios deve ser idempotente.
- Não devem ser introduzidas dependências circulares.

## 6. A IA não pode

A IA não pode:

- criar uma dependência que não esteja nas regras `allowed-to-use`;
- criar novos componentes ou mover responsabilidades entre componentes sem decisão arquitetural;
- criar novos serviços, bases de dados ou brokers sem um ADR;
- permitir que `desbloqueio` aceda diretamente a `viagens`;
- fazer `tarifacao` desencadear diretamente `cobranca`;
- fazer Reporting depender diretamente de `viagens`;
- colocar tarifários específicos hardcoded;
- assumir que eventos ou mensagens são entregues uma única vez;
- permitir novos desbloqueios offline;
- alterar comunicação síncrona para assíncrona, ou vice-versa, quando esta estiver definida por ADR;
- aceder à implementação interna de outro componente para contornar o seu contrato.

Se uma funcionalidade exigir violar uma destas regras, a IA deve sinalizar a necessidade de rever a arquitetura antes de gerar o código.

## 7. ADRs relevantes por componente

| Componente | ADRs relevantes |
|---|---|
| Utilizadores | ADR-002, ADR-003, ADR-004 |
| Desbloqueio | ADR-002, ADR-003, ADR-004 |
| Viagens | ADR-002, ADR-003, ADR-004 |
| Tarifação | ADR-002, ADR-004 |
| Cobrança | ADR-002, ADR-004 |
| Histórico de Viagens | ADR-004 |
| Faturação | ADR-004 |
| Comunicação das Docas | ADR-002, ADR-003, ADR-004 |
| Consulta de Estações | ADR-004 |
| Planeamento de Redistribuição | ADR-004 |
| Planeamento de Rotas | ADR-004 |
| Telemetria | ADR-004, ADR-005 |
| Manutenção | ADR-004, ADR-005 |
| Relatórios Municipais | ADR-001, ADR-004 |

### ADRs

- **ADR-001** — Reporting Municipal consulta diretamente a base de dados, apenas em leitura.
- **ADR-002** — o fluxo principal utiliza comunicação síncrona.
- **ADR-003** — novos desbloqueios exigem autorização online; devoluções podem ser sincronizadas após falhas de rede.
- **ADR-004** — infraestrutura cloud, múltiplas instâncias equivalentes do backend e balanceador de carga.
- **ADR-005** — Manutenção da Frota é executada separadamente e `Telemetria -> Manutenção` comunica através do broker.