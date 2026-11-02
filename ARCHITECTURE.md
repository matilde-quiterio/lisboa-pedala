# ARCHITECTURE — Lisboa Pedala

Este ficheiro define as regras arquiteturais que devem ser respeitadas por qualquer implementação ou código gerado por IA. As decisões detalhadas encontram-se em `docs/` e nos ADRs em `docs/adr/`.

## 1. Componentes

A arquitetura lógica é particionada por domínio. Cada componente tem uma responsabilidade única e vive no namespace indicado.

| Componente | Responsabilidade | Namespace |
|---|---|---|
| Utilizadores | Gerir identificação e dados da conta necessários ao acesso e tarifação. | `src.viagens.utilizadores` |
| Desbloqueio | Coordenar o acesso à bicicleta, solicitando a validação do utilizador, a preparação da viagem e o destrancamento da doca. | `src.viagens.desbloqueio` |
| Viagens | Gerir o registo e os estados das viagens, garantindo a exclusividade do utilizador e da bicicleta e coordenando a tarifação, cobrança e faturação, quando aplicáveis. | `src.viagens.viagens` |
| Tarifação | Calcular a tarifa aplicável a uma viagem. | `src.viagens.tarifacao` |
| Cobrança | Processar a cobrança ao utilizador. | `src.viagens.cobranca` |
| Histórico de Viagens | Disponibilizar ao utilizador as viagens realizadas. | `src.viagens.historico` |
| Faturação | Gerar, guardar e disponibilizar faturas associadas às viagens. | `src.viagens.faturacao` |
| Comunicação das Docas | Enviar comandos e receber eventos das docas, encaminhando-os para os componentes responsáveis. | `src.estacoes.comunicacao_docas` |
| Consulta de Estações | Disponibilizar bicicletas disponíveis e docas livres por estação. | `src.estacoes.consulta_estacoes` |
| Planeamento de Redistribuição | Determinar as quantidades de bicicletas a recolher e entregar em cada estação. | `src.redistribuicao.planeamento_redistribuicao` |
| Planeamento de Rotas | Calcular e disponibilizar as rotas das equipas de redistribuição. | `src.redistribuicao.planeamento_rotas` |
| Telemetria | Receber e processar os dados enviados pelas bicicletas elétricas. | `src.manutencao.telemetria` |
| Manutenção | Gerir reportes manuais de avaria e avarias identificadas pela Telemetria, ordens de manutenção e intervenções. | `src.manutencao.manutencao` |
| Relatórios Municipais | Consultar e agregar dados para produzir o relatório mensal municipal. | `src.reporting.relatorios_municipais` |

## 2. Regras allowed-to-use

Apenas são permitidas as seguintes dependências entre componentes:

```text
desbloqueio -> utilizadores
desbloqueio -> viagens
desbloqueio -> comunicacao_docas

comunicacao_docas -> viagens
comunicacao_docas -> consulta_estacoes

viagens -> tarifacao
viagens -> cobranca
viagens -> faturacao

tarifacao -> utilizadores
cobranca -> utilizadores

historico -> viagens


planeamento_redistribuicao -> consulta_estacoes
planeamento_redistribuicao -> planeamento_rotas

telemetria -> manutencao
```

`relatorios_municipais` não depende de outros componentes e pode consultar diretamente a base de dados partilhada apenas em leitura.

**Qualquer dependência entre componentes não listada acima é proibida.**

Em particular:

- `tarifacao` não pode depender de `cobranca`;
- `relatorios_municipais` não pode depender de `viagens`;
- `faturacao` não pode depender de `viagens` nem de `cobranca`, pois recebe os dados necessários no pedido de emissão enviado por `viagens`;
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
- os eventos de retirada e devolução devem poder ser associados à viagem mesmo quando chegam fora de ordem;
- a hora de início corresponde ao instante da retirada registado pela doca, mesmo que o evento seja recebido posteriormente.

### Configurability

A plataforma deve suportar tarifários próprios de diferentes municípios sem alterar a lógica central.

Implicações para o código:

- tarifários e valores específicos de um município não podem estar hardcoded;
- `tarifacao` deve receber ou obter a configuração aplicável ao município;
- a alteração de um tarifário não deve exigir alterações nos restantes componentes.

## 4. Acoplamento temporal e unidades de trabalho

O fluxo principal deve respeitar esta ordem:

```text
identificar e validar utilizador
-> solicitar a Viagens a preparação da viagem
-> verificar exclusividade do utilizador e da bicicleta e guardar viagem pendente de retirada
-> autorizar desbloqueio
-> solicitar destrancamento através de Comunicação das Docas
-> confirmar destrancamento
-> receber confirmação da retirada da bicicleta
-> passar viagem a em curso, usando a hora da retirada
-> receber confirmação de encaixe na doca
-> fechar viagem e guardar os respetivos dados, usando a hora do encaixe
-> calcular tarifa
-> cobrar, se aplicável
-> emitir e guardar fatura, se aplicável
```

Regras obrigatórias:

1. Desbloqueio solicita a preparação a Viagens antes de pedir o destrancamento a Comunicação das Docas. Se a preparação for recusada, não é enviado o comando à doca.
2. Viagens verifica que nem o utilizador nem a bicicleta estão associados a outra viagem pendente ou em curso e cria o registo pendente numa única transação.
3. O registo pendente associa utilizador e bicicleta, mas não inicia a contagem do tempo.
4. A viagem só passa a estar em curso após receber a confirmação da retirada. A hora de início corresponde ao instante físico registado pela doca.
5. A viagem só é fechada após receber a confirmação de encaixe. A hora de fim corresponde ao instante físico registado pela doca.
6. A tarifa só pode ser calculada depois de a viagem estar fechada.
7. A cobrança só pode ocorrer depois de a tarifa ter sido calculada. Se a tarifa for zero, não é efetuada cobrança.
8. O processamento repetido do mesmo evento não pode duplicar uma viagem, uma cobrança nem uma fatura.

Dentro de `Viagens`, o registo de um evento como processado e a atualização correspondente da viagem devem ocorrer na mesma transação, evitando perder a atualização ou aplicá-la novamente após uma falha.

O fecho da viagem, a tarifação, a cobrança e a faturação respeitam uma ordem temporal, mas não constituem uma única transação. O fecho é confirmado na base de dados antes das operações seguintes e não é desfeito se estas falharem.

### Prazo de retirada

Após o destrancamento, o utilizador dispõe de um prazo configurável para retirar a bicicleta. A viagem só é iniciada se a doca confirmar a retirada.

Se o prazo terminar sem retirada, a doca tenta voltar a bloquear a bicicleta. Após receber a confirmação de que não houve retirada e de que a bicicleta está bloqueada, Viagens cancela o registo pendente, permitindo uma nova utilização sem iniciar nem cobrar uma viagem.

O controlo do prazo e a tentativa de bloqueio são executados localmente pela doca simulada, mesmo que entretanto perca a ligação ao backend.

### Falhas no desbloqueio e devolução

O registo pendente é guardado antes do envio do comando de destrancamento, preservando a associação entre utilizador, bicicleta e viagem caso a comunicação falhe.

Se a doca confirmar que o destrancamento falhou, Viagens cancela o registo pendente e permite nova tentativa. Se a doca não responder dentro de um tempo limite configurável (timeout), a chamada termina com resultado por confirmar e o registo mantém-se pendente. O timeout não implica que a operação física falhou. Enquanto existir uma viagem pendente ou em curso, não é autorizado outro desbloqueio para o mesmo utilizador ou bicicleta.

Durante falhas de ligação, as docas guardam os eventos e reenviam-nos quando recuperam a comunicação. Cada evento inclui um identificador único, o identificador da bicicleta, a doca ou estação e o instante físico da ocorrência. Comunicação das Docas encaminha os eventos para Viagens, que utiliza a associação previamente guardada para identificar a viagem correspondente, mesmo quando a devolução ocorre noutra estação.

Os eventos podem chegar atrasados ou fora de ordem. Se a devolução chegar antes da retirada, é guardada até receber o evento em falta. Quando ambos estiverem disponíveis, a viagem fica terminada, usando a hora da retirada como início e a hora do encaixe como fim. Só depois se desencadeiam a tarifação, cobrança e faturação, quando aplicáveis.

A associação dos eventos deve respeitar os seus identificadores e instantes físicos, evitando que um evento antigo seja aplicado a uma utilização posterior da mesma bicicleta. Os reenvios não podem duplicar viagens nem operações financeiras.

### Tratamento de avarias

No fluxo `Telemetria -> Manutenção`, a comunicação é assíncrona: Telemetria publica a mensagem no broker e não espera pela criação da ordem de manutenção.

Os reportes manuais são recebidos diretamente por Manutenção através da CLI/API. Tanto estes como as avarias comunicadas por Telemetria originam ordens pendentes de avaliação pelo técnico.

O técnico determina se é necessária uma intervenção. Manutenção guarda a ordem, a avaliação do técnico, os dados da intervenção realizada, quando aplicável, e o resultado registado no fecho.

### Seleção do meio de pagamento

O utilizador escolhe entre cartão associado e MB WAY. `viagens` transmite essa escolha e os dados necessários no pedido a `cobranca`.

No pagamento com cartão associado, `cobranca` consulta `utilizadores` para obter a referência do cartão. No pagamento por MB WAY, utiliza os dados fornecidos no pedido.

Ter um cartão associado não impede escolher MB WAY.

## 5. Convenções de código

- O código é organizado primeiro por domínio: `viagens`, `estacoes`, `redistribuicao`, `manutencao` e `reporting`.
- Cada componente deve manter apenas a responsabilidade definida na secção 1.
- Dependências entre componentes devem respeitar estritamente a secção 2.
- A comunicação entre componentes deve ser feita através de contratos explícitos.
- O fluxo `desbloquear -> devolver -> cobrar -> faturar` utiliza comunicação síncrona.
- `Telemetria -> Manutenção` utiliza comunicação assíncrona através do broker.
- A lógica de tarifação pertence exclusivamente a `tarifacao`.
- A coordenação entre fecho da viagem, tarifação, cobrança e faturação pertence a `viagens`.
- A comunicação física com as docas pertence a `comunicacao_docas`.
- Reporting apenas pode escrever o seu próprio resultado; o acesso aos dados operacionais é read-only.
- Código para tratamento de reenvios deve ser idempotente.
- Não devem ser introduzidas dependências circulares.
- A interação com as docas é simulada, incluindo comandos de desbloqueio, confirmações e reenvio de eventos após falhas de ligação.
- Os pagamentos por cartão ou MB WAY são simulados em `cobranca`, sem integração com prestadores externos.
- A leitura e validação do cartão Navegante são simuladas através de identificadores fictícios previamente definidos, sem integração com entidades externas.

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