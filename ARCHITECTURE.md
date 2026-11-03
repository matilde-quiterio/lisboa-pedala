# ARCHITECTURE — Lisboa Pedala

Este ficheiro define as regras arquiteturais obrigatórias para qualquer implementação ou código gerado por IA. As decisões detalhadas encontram-se em `docs/` e nos ADRs em `docs/adr/`.

## 1. Componentes

A arquitetura lógica é particionada por domínio.

| Componente | Responsabilidade | Namespace |
|---|---|---|
| Utilizadores | Gerir identificação e dados da conta necessários ao acesso e tarifação. | `src.viagens.utilizadores` |
| Desbloqueio | Coordenar a validação do utilizador, preparação da viagem e destrancamento da doca. | `src.viagens.desbloqueio` |
| Viagens | Gerir o ciclo de vida das viagens, exclusividade de utilizador/bicicleta e coordenar tarifação, cobrança e faturação quando aplicáveis. | `src.viagens.viagens` |
| Tarifação | Calcular a tarifa aplicável a uma viagem. | `src.viagens.tarifacao` |
| Cobrança | Processar a cobrança ao utilizador. | `src.viagens.cobranca` |
| Histórico de Viagens | Disponibilizar as viagens realizadas pelo utilizador. | `src.viagens.historico` |
| Faturação | Gerar, guardar e disponibilizar faturas associadas às viagens. | `src.viagens.faturacao` |
| Comunicação das Docas | Enviar comandos e receber eventos das docas. | `src.estacoes.comunicacao_docas` |
| Consulta de Estações | Disponibilizar bicicletas e docas livres por estação. | `src.estacoes.consulta_estacoes` |
| Planeamento de Redistribuição | Determinar quantidades de bicicletas a recolher e entregar. | `src.redistribuicao.planeamento_redistribuicao` |
| Planeamento de Rotas | Calcular e disponibilizar rotas de redistribuição. | `src.redistribuicao.planeamento_rotas` |
| Telemetria | Receber e processar dados das bicicletas elétricas. | `src.manutencao.telemetria` |
| Manutenção | Gerir reportes de avaria, ordens de manutenção e intervenções. | `src.manutencao.manutencao` |
| Relatórios Municipais | Consultar e agregar dados para o relatório mensal municipal. | `src.reporting.relatorios_municipais` |

## 2. Regras allowed-to-use

São permitidas apenas as seguintes dependências:

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

**Qualquer dependência entre componentes não listada é proibida.**

Em particular:

- `tarifacao` não pode depender de `cobranca`;
- `relatorios_municipais` não pode depender de `viagens`;
- `faturacao` não pode depender de `viagens` nem de `cobranca`; recebe no pedido os dados necessários;
- os restantes componentes não podem depender de `relatorios_municipais`.

O mecanismo de comunicação não altera estas regras.

### Contratos entre componentes

As regras `allowed-to-use` aplicam-se também aos tipos usados nos contratos.

Um componente não pode importar modelos, DTOs, enums ou outros tipos internos de outro componente quando essa dependência não está permitida.

Quando necessário, os contratos devem usar tipos simples ou estruturas próprias do componente que expõe o contrato.

## 3. Características arquiteturais prioritárias

### Availability

O desbloqueio deve manter elevada disponibilidade devido à penalização contratual associada à indisponibilidade das estações.

Implicações:

- o backend deve poder executar em múltiplas instâncias equivalentes;
- estado necessário a pedidos posteriores não pode depender apenas de memória local;
- operações repetidas devem evitar efeitos duplicados;
- a falha de uma instância não pode impedir outra de continuar a servir pedidos;
- novos desbloqueios exigem comunicação e autorização do backend, conforme ADR-003.

### Persistência do esqueleto funcional

O esqueleto funcional usa SQLite como implementação local da base de dados partilhada.

Estado necessário entre pedidos não pode existir apenas em memória.

A verificação de que utilizador e bicicleta não possuem outra viagem `PENDENTE` ou `EM_CURSO` e a criação da nova viagem `PENDENTE` devem ocorrer na mesma transação.

SQLite aplica-se apenas ao esqueleto funcional e não altera a decisão de deployment do ADR-004.

### Robustness

O sistema deve tolerar falhas temporárias de comunicação e reenvio de eventos.

Implicações:

- eventos das docas devem ser processados de forma idempotente;
- o mesmo evento não pode iniciar ou fechar uma viagem mais do que uma vez;
- início e fim da viagem usam os instantes físicos registados pela doca;
- eventos atrasados ou fora de ordem devem poder ser associados à viagem correta;
- mensagens de avaria repetidas não podem criar ordens duplicadas;
- falhas de comunicação devem ser tratadas explicitamente.

### Configurability

A plataforma deve permitir tarifários diferentes por município sem alterar a lógica central.

Implicações:

- valores específicos de um município não podem estar hardcoded;
- `tarifacao` recebe ou obtém a configuração aplicável;
- alterar um tarifário não deve exigir alterações noutros componentes.

Para assinantes com passe anual, cada viagem inclui 45 minutos gratuitos e, depois disso, é cobrada por blocos de 15 minutos. O preço de cada bloco pertence à configuração do município. Cada bloco de 15 minutos iniciado após os 45 minutos gratuitos é cobrado por inteiro. Assim, qualquer duração superior a 45 minutos origina pelo menos um bloco cobrado.

## 4. Acoplamento temporal e unidades de trabalho

O fluxo principal deve respeitar:

```text
identificar e validar utilizador
-> solicitar a Viagens a preparação da viagem
-> verificar exclusividade e criar viagem PENDENTE
-> solicitar destrancamento através de Comunicação das Docas
-> confirmar destrancamento
-> receber confirmação de retirada
-> passar viagem a EM_CURSO usando o instante físico da retirada
-> receber confirmação de encaixe
-> terminar viagem usando o instante físico do encaixe
-> calcular tarifa
-> cobrar, se aplicável
```

Regras obrigatórias:

1. `Desbloqueio` pede a preparação a `Viagens` antes do destrancamento.
2. `Viagens` verifica a exclusividade do utilizador e da bicicleta e cria a viagem `PENDENTE` na mesma transação.
3. Os eventos de retirada e devolução devem ser correlacionados com a utilização criada antes do destrancamento através de um identificador comum, conforme ADR-003.
4. O estado `PENDENTE` associa utilizador e bicicleta, mas não inicia a contagem da viagem.
5. O destrancamento não inicia a viagem.
6. A viagem passa a `EM_CURSO` apenas após confirmação da retirada física.
7. A viagem termina apenas após confirmação do encaixe físico.
8. O registo do evento como processado e a atualização correspondente da viagem ocorrem na mesma transação.
9. A tarifa é calculada apenas depois do fecho da viagem.
10. A cobrança ocorre apenas depois da tarifa; tarifa zero não origina cobrança.
11. Eventos repetidos não podem duplicar viagens, cobranças ou faturas.

O fecho, a tarifação e a cobrança respeitam esta ordem, mas não formam uma única transação. Uma viagem já terminada não é reaberta se a tarifação ou a cobrança falharem. A faturação é uma responsabilidade posterior de `Faturação` e não faz parte do fluxo obrigatório da US-1.

### Prazo de retirada

Após o destrancamento existe um prazo configurável para retirar a bicicleta.

Se o prazo terminar sem retirada, a doca tenta voltar a bloquear a bicicleta.

Quando é confirmado que não ocorreu retirada e que a bicicleta ficou bloqueada, `Viagens` cancela a viagem `PENDENTE`.

O controlo do prazo e a tentativa de bloqueio são executados localmente pela doca simulada, mesmo se esta perder entretanto a ligação ao backend.

### Falhas no desbloqueio e devolução

A viagem `PENDENTE` é criada antes do envio do comando de destrancamento.

Se a doca confirmar que o destrancamento falhou, a viagem pendente é cancelada.

Se não houver resposta dentro do timeout configurável, o resultado fica por confirmar e a viagem mantém-se `PENDENTE`. Timeout não significa falha física.

Enquanto existir uma viagem `PENDENTE` ou `EM_CURSO`, não é permitido novo desbloqueio para o mesmo utilizador ou bicicleta.

Durante falhas de rede, as docas guardam eventos e reenviam-nos quando a comunicação é restabelecida.

Cada evento inclui:

- identificador único do evento;
- identificador da utilização a que pertence;
- bicicleta;
- doca ou estação;
- instante físico.

`Comunicação das Docas` encaminha os eventos para `Viagens`. Os eventos de retirada e devolução transportam um identificador comum à utilização criada antes do destrancamento, permitindo a `Viagens` determinar inequivocamente a viagem correspondente, conforme ADR-003.

Os eventos podem chegar atrasados ou fora de ordem. Se a devolução chegar antes da retirada, é guardada até chegar o evento em falta. Quando ambos existem, a viagem termina usando os respetivos instantes físicos.

Um evento antigo não pode ser aplicado a uma utilização posterior da mesma bicicleta.

### Tratamento de avarias

No fluxo `Telemetria -> Manutenção`, a comunicação é assíncrona através do broker.

Reportes manuais são recebidos diretamente por `Manutenção`.

Reportes manuais ou avarias provenientes da Telemetria criam ordens pendentes de avaliação pelo técnico.

O técnico avalia a necessidade de intervenção e `Manutenção` guarda a avaliação, intervenção quando aplicável e resultado final.

Cada ordem começa em `PENDENTE_AVALIACAO`. Se não for necessária intervenção, `Manutenção` regista a avaliação e o resultado, e fecha a ordem em
`SEM_INTERVENCAO_NECESSARIA`. Se for necessária, a ordem passa a `EM_INTERVENCAO`; após a intervenção, esta e o resultado são registados e a ordem passa a `CONCLUIDA`. Este workflow não usa o estado `CANCELADA`.

### Seleção do meio de pagamento

O utilizador pode escolher cartão associado ou MB WAY.

`Viagens` transmite a escolha e os dados necessários a `Cobrança`.

No pagamento com cartão associado, `Cobrança` consulta `Utilizadores` para obter a referência do cartão.

No pagamento por MB WAY, utiliza os dados fornecidos no pedido.

Ter um cartão associado não impede a utilização de MB WAY.

No esqueleto funcional, a cobrança é simulada deterministicamente: um pagamento é considerado aceite quando existem os dados necessários ao meio de pagamento escolhido; a ausência desses dados origina falha da cobrança. A mesma chave de idempotência não pode produzir mais do que uma cobrança.

## 5. Convenções de código

- O código é organizado primeiro por domínio: `viagens`, `estacoes`, `redistribuicao`, `manutencao` e `reporting`.
- Cada componente mantém apenas a responsabilidade definida na secção 1.
- Dependências entre componentes respeitam estritamente a secção 2.
- A comunicação entre componentes usa contratos explícitos.
- O fluxo `desbloquear -> devolver -> cobrar` usa comunicação síncrona.
- `Telemetria -> Manutenção` usa comunicação assíncrona através do broker.
- A lógica de cálculo da tarifa pertence exclusivamente a `tarifacao`.
- A coordenação de fecho, tarifação, cobrança e faturação pertence a `viagens`.
- A comunicação física com as docas pertence a `comunicacao_docas`.
- Reporting acede aos dados operacionais apenas em leitura.
- Reenvios devem ser processados de forma idempotente.
- Não são permitidas dependências circulares.
- A interação com as docas é simulada, incluindo comandos, confirmações e reenvio de eventos.
- Pagamentos por cartão ou MB WAY são simulados em `cobranca`.
- A leitura e validação do cartão Navegante usam identificadores fictícios previamente definidos.
- O esqueleto funcional utiliza uma CLI simples; a CLI não contém lógica de negócio.

No esqueleto funcional, existem utilizadores fictícios previamente configurados. Um utilizador é autorizado quando existe e está marcado como ativo; utilizadores inexistentes ou inativos são rejeitados.

## 6. A IA não pode

A IA não pode:

- criar dependências não previstas nas regras `allowed-to-use`;
- criar novos componentes ou mover responsabilidades sem decisão arquitetural;
- criar novos serviços, bases de dados ou brokers sem ADR;
- fazer `tarifacao` desencadear diretamente `cobranca`;
- fazer Reporting depender de `viagens`;
- fazer `faturacao` consultar diretamente `viagens` ou `cobranca`;
- hardcodar valores específicos de tarifários;
- assumir entrega única de eventos ou mensagens;
- permitir novos desbloqueios offline;
- alterar comunicação síncrona para assíncrona, ou vice-versa, quando definida por ADR;
- aceder à implementação interna de outro componente para contornar contratos;
- introduzir tipos internos de outro componente quando isso cria uma dependência proibida.

Se uma funcionalidade exigir violar uma destas regras, a IA deve sinalizar a necessidade de rever a arquitetura antes de gerar código.

## 7. ADRs relevantes por componente

| Componente | ADRs relevantes |
|---|---|
| Utilizadores | ADR-002, ADR-003, ADR-004 |
| Desbloqueio | ADR-002, ADR-003, ADR-004 |
| Viagens | ADR-002, ADR-003, ADR-004 |
| Tarifação | ADR-002, ADR-004 |
| Cobrança | ADR-002, ADR-004 |
| Histórico de Viagens | ADR-004 |
| Faturação | ADR-002, ADR-004 |
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
- **ADR-003** — novos desbloqueios exigem autorização online; a viagem é preparada antes do destrancamento e inicia apenas após retirada física.
- **ADR-004** — infraestrutura cloud, múltiplas instâncias equivalentes do backend e balanceador de carga.
- **ADR-005** — Manutenção da Frota é executada separadamente e `Telemetria -> Manutenção` comunica através do broker.