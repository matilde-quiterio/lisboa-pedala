# 02 - Componentes Lógicos

## 1. Abordagem escolhida

Foi escolhida a abordagem **Workflow**.

Esta abordagem permite observar primeiro os principais fluxos do sistema de ponta a ponta e, a partir daí, identificar e separar os diferentes passos que podem dar origem a componentes lógicos.

No Lisboa Pedala, esta abordagem ajuda a perceber a sequência completa das operações principais, como desbloquear uma bicicleta, realizar a viagem, devolver a bicicleta e efetuar a cobrança, facilitando depois a divisão dessas responsabilidades em componentes.

## 2. Workflows principais

### Workflow 1 — Realizar uma viagem

desbloquear bicicleta
→ iniciar viagem
→ devolver bicicleta
→ fechar viagem
→ calcular tarifa
→ cobrar, se aplicável

### Workflow 2 — Processar telemetria

bicicleta elétrica envia telemetria
→ sistema recebe dados
→ atualiza estado da bicicleta

### Workflow 3 — Tratar manutenção

receber reporte de avaria
→ abrir ordem de manutenção
→ disponibilizar ordem ao técnico

### Workflow 4 — Consultar estado das estações

abrir aplicação
→ consultar mapa em tempo real
→ visualizar bicicletas disponíveis e docas livres por estação

### Workflow 5 — Gerar relatório municipal

chegar ao fim do período mensal
→ agregar dados de utilização
→ calcular indicadores por freguesia
→ produzir relatório para a Câmara

### Workflow 6 — Consultar histórico e faturas

abrir aplicação
→ consultar histórico de viagens
→ consultar faturas

### Workflow 7 — Redistribuir bicicletas

detetar desequilíbrio na ocupação das estações
→ sugerir rota às carrinhas de redistribuição
→ equilibrar a ocupação das estações

## 3. Mapeamento das user stories para componentes

| User story | Descrição | Componentes envolvidos |
|---|---|---|
| US-1 | Como assinante, desbloqueio e devolvo uma bicicleta e a viagem fica registada e cobrada. | Desbloqueio, Comunicação das Docas, Viagens, Tarifação, Cobrança |
| US-2 | Como técnico, recebo uma ordem de manutenção quando uma bicicleta reporta avaria. | Telemetria, Manutenção |
| US-3 | Como doca sem rede, reenvio os eventos guardados quando a rede volta, sem duplicar viagens. | Comunicação das Docas, Viagens |
| US-4 | Como gestor municipal, obtenho o relatório de utilização por freguesia. | Relatórios Municipais |

## 4. Componentes lógicos    e responsabilidades

- **Desbloqueio** — valida e executa o desbloqueio de uma bicicleta.
- **Viagens** — regista e mantém o estado da viagem de um utilizador.
- **Tarifação** — calcula a tarifa aplicável a uma viagem.
- **Cobrança** — processa a cobrança ao utilizador.
- **Manutenção** — recebe reportes de avaria e cria ordens de manutenção para os técnicos.
- **Consulta de Estações** — disponibiliza o estado das estações, incluindo bicicletas disponíveis e docas livres.
- **Relatórios Municipais** — agrega os dados necessários e produz o relatório mensal para a Câmara.
- **Telemetria** — recebe e processa a telemetria enviada pelas bicicletas elétricas.
- **Histórico de Viagens** — disponibiliza ao utilizador o histórico das viagens realizadas.
- **Faturação** — gera e disponibiliza as faturas associadas às viagens, com os dados da viagem e da cobrança.
- **Comunicação das Docas** — gere a comunicação com as docas e recebe os eventos enviados por estas.
- **Redistribuição** — analisa o desequilíbrio na ocupação das estações e sugere rotas às carrinhas para redistribuir bicicletas.

## 5. Análise de coesão

De forma geral, os componentes definidos apresentam boa coesão, uma vez que cada um concentra responsabilidades relacionadas com uma função específica do sistema.

Por exemplo, Desbloqueio trata apenas do processo de desbloqueio, Viagens concentra o registo e estado das viagens, Tarifação calcula os valores aplicáveis, e Manutenção trata dos reportes de avaria e ordens de manutenção.

A separação entre componentes como Viagens, Tarifação, Cobrança, Faturação e Histórico de Viagens evita concentrar responsabilidades distintas num único componente, reduzindo o risco de baixa coesão.

Da mesma forma, Comunicação das Docas, Telemetria, Consulta de Estações e Redistribuição têm responsabilidades distintas, apesar de trabalharem sobre informação relacionada com bicicletas e estações.

A decomposição não foi feita apenas com base nas entidades do domínio, mas sim nos workflows e responsabilidades do sistema, evitando assim a Entity Trap.

## 6. Acoplamento estático e instabilidade

A instabilidade é calculada através de:

I = CE / (CA + CE)

| Componente | Depende de | CA | CE | Instabilidade |
|---|---|---:|---:|---:|
| Desbloqueio | Comunicação das Docas | 0 | 1 | 1 |
| Viagens | — | 5 | 0 | 0 |
| Tarifação | Viagens | 1 | 1 | 0,5 |
| Cobrança | Tarifação | 1 | 1 | 0,5 |
| Telemetria | Manutenção | 0 | 1 | 1 |
| Manutenção | — | 1 | 0 | 0 |
| Comunicação das Docas | Viagens, Consulta de Estações | 1 | 2 | 0,67 |
| Consulta de Estações | — | 2 | 0 | 0 |
| Redistribuição | Consulta de Estações | 0 | 1 | 1 |
| Histórico de Viagens | Viagens | 0 | 1 | 1 |
| Faturação | Cobrança, Viagens | 0 | 2 | 1 |
| Relatórios Municipais | Viagens | 0 | 1 | 1 |

Valores próximos de 0 indicam componentes mais estáveis, enquanto valores próximos de 1 indicam componentes mais instáveis.

## 7. Acoplamento temporal

### Exemplo 1 — Devolução da bicicleta

A confirmação de encaixe da doca tem de ser recebida antes de a viagem poder ser fechada.

### Exemplo 2 — Cobrança da viagem

A viagem tem de estar fechada antes de a tarifa poder ser calculada, e a tarifa tem de ser calculada antes de a cobrança ser efetuada.

## 8. Conascência

Existe conascência entre os componentes **Tarifação** e **Cobrança**, porque a Cobrança depende da informação produzida pela Tarifação para processar o pagamento.

Os dois componentes têm de concordar sobre a representação do valor a cobrar, nomeadamente a moeda, o arredondamento e o montante associado à viagem. Uma alteração nesse contrato pode obrigar a alterações em ambos os componentes.

## 9. Iteração de reestruturação

Na decomposição inicial, os eventos enviados pelas docas não tinham um componente próprio.

Durante o mapeamento da US-3, verificou-se que a responsabilidade de receber e gerir os eventos das docas não pertencia ao componente Telemetria, que trata apenas dos dados enviados pelas bicicletas elétricas, nem ao componente Viagens.

Por esse motivo, foi criado o componente **Comunicação das Docas**, responsável por gerir a comunicação com as docas e receber os eventos enviados por estas.

Esta alteração melhorou a separação de responsabilidades e evitou sobrecarregar os componentes Telemetria e Viagens.

## 10. Lei de Deméter

A arquitetura procura limitar o conhecimento entre componentes, fazendo com que cada componente interaja apenas com aqueles de que necessita diretamente.

Por exemplo, o componente Desbloqueio comunica com Comunicação das Docas para executar o desbloqueio, não conhecendo diretamente o componente Viagens. Depois da confirmação da doca, Comunicação das Docas informa Viagens para iniciar a viagem.

Desta forma, Desbloqueio não precisa de conhecer componentes que não são diretamente necessários à sua responsabilidade, reduzindo o acoplamento.