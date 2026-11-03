# ARCHITECTURE — Lisboa Pedala

Este ficheiro define as regras arquiteturais obrigatórias para qualquer implementação ou código gerado por IA. O detalhe e a justificação das decisões encontram-se em `docs/` e `docs/adr/`.

## 1. Componentes

A arquitetura lógica é particionada por domínio.

| Componente | Responsabilidade | Namespace |
|---|---|---|
| Utilizadores | Gerir identificação e dados da conta necessários ao acesso e tarifação. | `src.viagens.utilizadores` |
| Desbloqueio | Coordenar validação do utilizador, preparação da viagem e destrancamento da doca. | `src.viagens.desbloqueio` |
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

## 2. Regras `allowed-to-use`

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

Qualquer dependência não listada é proibida.

Estas regras aplicam-se também aos contratos: um componente não pode importar tipos internos de outro componente quando essa dependência não está permitida. Os contratos usam tipos simples ou estruturas próprias do componente que os expõe.

## 3. Características arquiteturais prioritárias

### Availability

O desbloqueio deve manter elevada disponibilidade.

Implicações:
- o backend pode executar em múltiplas instâncias equivalentes;
- estado necessário entre pedidos não pode depender apenas de memória local;
- novos desbloqueios exigem comunicação e autorização do backend, conforme ADR-003.

### Robustness

O sistema deve tolerar falhas temporárias de comunicação e reenvio de eventos.

Implicações:
- eventos são processados de forma idempotente;
- início e fim usam os instantes físicos registados pela doca;
- eventos atrasados, repetidos ou fora de ordem não podem duplicar efeitos nem ser associados à utilização errada.

### Configurability

Os tarifários municipais não podem estar hardcoded.

`Tarifação` recebe ou obtém a configuração aplicável. Para passe anual, cada viagem inclui 45 minutos gratuitos; depois, cada bloco de 15 minutos iniciado é cobrado por inteiro. O preço do bloco pertence à configuração municipal.

## 4. Persistência e acoplamento temporal

O esqueleto funcional usa SQLite como implementação local da base de dados partilhada. Estado necessário entre pedidos não pode existir apenas em memória.

O fluxo principal respeita:

```text
identificar e validar utilizador
-> preparar viagem
-> verificar exclusividade e criar PENDENTE
-> solicitar destrancamento
-> receber retirada física
-> passar a EM_CURSO
-> receber encaixe físico
-> terminar viagem
-> calcular tarifa
-> cobrar, se aplicável
```

Regras obrigatórias:

1. `Desbloqueio` valida o utilizador e pede a `Viagens` a preparação antes do destrancamento.
2. A verificação de exclusividade de utilizador/bicicleta e a criação da viagem `PENDENTE` ocorrem na mesma transação.
3. Destrancar não inicia a viagem; apenas a retirada física muda `PENDENTE -> EM_CURSO`.
4. A viagem termina apenas após confirmação do encaixe físico.
5. Retirada e devolução são correlacionadas com a utilização através de um identificador comum e processadas idempotentemente.
6. O registo do evento e a atualização correspondente da viagem ocorrem na mesma transação.
7. A tarifa é calculada apenas depois do fecho; tarifa zero não origina cobrança.
8. Fecho, tarifação e cobrança respeitam esta ordem, mas não formam uma única transação.
9. Se tarifação ou cobrança falharem, a viagem permanece `TERMINADA`; o retry usa o estado persistido, sem reprocessar o evento físico, e mantém a mesma chave de idempotência.
10. Eventos repetidos não podem duplicar viagens, cobranças ou faturas.

Prazo de retirada, falhas de destrancamento, resultados desconhecidos, rebloqueio local, armazenamento/reenvio de eventos e eventos fora de ordem seguem o ADR-003.

A faturação é posterior e não faz parte do fluxo obrigatório da US-1.

## 5. Regras funcionais do esqueleto

- Utilizadores fictícios são autorizados quando existem e estão ativos; QR e cartão Navegante são simulados através de identificadores fictícios.
- O utilizador pode escolher cartão associado ou MB WAY.
- `Cobrança` consulta `Utilizadores` para cartão associado; MB WAY usa os dados fornecidos no pedido.
- A cobrança simulada é aceite quando existem os dados necessários; caso contrário falha.
- A mesma chave de idempotência não pode produzir mais do que uma cobrança.
- A interação com docas e pagamentos é simulada.
- `Telemetria -> Manutenção` usa comunicação assíncrona através do broker; o restante comportamento segue o ADR-005.

## 6. Convenções de código

- O código é organizado por domínio: `viagens`, `estacoes`, `redistribuicao`, `manutencao` e `reporting`.
- A comunicação entre componentes usa contratos explícitos.
- `desbloquear -> devolver -> cobrar` usa comunicação síncrona.
- `Telemetria -> Manutenção` usa comunicação assíncrona através do broker.
- A lógica de tarifa pertence exclusivamente a `tarifacao`.
- A coordenação de fecho, tarifação, cobrança e faturação pertence a `viagens`.
- A comunicação física com as docas pertence a `comunicacao_docas`.
- Reporting acede aos dados operacionais apenas em leitura.
- A CLI é simples e não contém lógica de negócio.

## 7. A IA não pode

A IA não pode:

- criar ou contornar dependências não previstas em `allowed-to-use`;
- criar componentes ou mover responsabilidades sem decisão arquitetural;
- criar novos serviços, bases de dados ou brokers sem ADR;
- fazer `tarifacao` desencadear diretamente `cobranca`;
- fazer Reporting depender de `viagens`;
- fazer `faturacao` consultar diretamente `viagens` ou `cobranca`;
- hardcodar valores específicos de tarifários;
- assumir entrega única de eventos ou mensagens;
- permitir novos desbloqueios offline;
- alterar comunicação síncrona para assíncrona, ou vice-versa, quando definida por ADR.

Se uma funcionalidade exigir violar estas regras, a arquitetura deve ser revista antes da geração de código.

## 8. ADRs relevantes

| Componentes | ADRs |
|---|---|
| Utilizadores, Desbloqueio, Viagens, Comunicação das Docas | ADR-002, ADR-003, ADR-004 |
| Tarifação, Cobrança, Faturação | ADR-002, ADR-004 |
| Histórico de Viagens | ADR-004 |
| Consulta de Estações, Planeamento de Redistribuição, Planeamento de Rotas | ADR-004 |
| Telemetria, Manutenção | ADR-004, ADR-005 |
| Relatórios Municipais | ADR-001, ADR-004 |