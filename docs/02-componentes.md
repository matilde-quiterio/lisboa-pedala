# 02 - Componentes Lógicos

## 1. Abordagem escolhida

Foi escolhida a abordagem **Workflow**.

Esta abordagem permite observar primeiro os principais fluxos do sistema de ponta a ponta e, a partir daí, identificar e separar os diferentes passos que podem dar origem a componentes lógicos.

No Lisboa Pedala, esta abordagem ajuda a perceber a sequência completa das operações principais, como desbloquear uma bicicleta, realizar a viagem, devolver a bicicleta e efetuar a cobrança, facilitando depois a divisão dessas responsabilidades em componentes.

## 2. Workflows principais

### Workflow  1 — Associar cartão Navegante 

utilizador autenticado solicita associação do cartão
→ sistema obtém o identificador do cartão
→ verifica se já está associado a outra conta
→ associa o cartão à conta do utilizador

### Workflow 2 — Realizar uma viagem

pedir desbloqueio pela app através de QR ou com o cartão Navegante
→ identificar e validar utilizador
→ desbloquear bicicleta
→ iniciar viagem
→ devolver bicicleta
→ fechar viagem e guardar os respetivos dados para consulta no histórico
→ calcular tarifa
→ cobrar, se aplicável
→ emitir fatura, se aplicável

### Workflow 3 — Processar telemetria

bicicleta elétrica envia telemetria  
→ sistema recebe dados  
→ atualiza estado da bicicleta

### Workflow 4 — Tratar manutenção

receber reporte manual de avaria ou avaria identificada pela telemetria
→ abrir ordem de manutenção pendente de avaliação
→ disponibilizar ordem ao técnico
→ técnico avalia a necessidade de intervenção
→ realizar e registar a intervenção, se necessária
→ fechar ordem e registar o resultado

### Workflow 5 — Consultar estado das estações

abrir aplicação  
→ consultar mapa em tempo real  
→ visualizar bicicletas disponíveis e docas livres por estação

### Workflow 6 — Gerar relatório municipal

chegar ao fim do período mensal  
→ agregar dados de utilização  
→ calcular indicadores por freguesia  
→ produzir relatório para a Câmara

### Workflow 7 — Consultar histórico e faturas

abrir aplicação  
→ consultar histórico de viagens  
→ consultar faturas

### Workflow 8 — Redistribuir bicicletas

detetar desequilíbrio na ocupação das estações que ultrapasse o limiar configurado
→ calcular as quantidades de bicicletas a recolher e entregar em cada estação
→ planear as rotas das carrinhas de redistribuição
→ disponibilizar o plano às equipas de redistribuição
→ equipas executam as recolhas e entregas

## 3. Mapeamento das user stories para componentes

| User story | Descrição | Componentes envolvidos |
|---|---|---|
| US-1 | Como assinante, desbloqueio e devolvo uma bicicleta e a viagem fica registada e cobrada. | Utilizadores, Desbloqueio, Comunicação das Docas, Viagens, Tarifação, Cobrança |
| US-2 | Como técnico, recebo uma ordem de manutenção quando uma bicicleta reporta avaria. | Telemetria, Manutenção |
| US-3 | Como doca sem rede, reenvio os eventos guardados quando a rede volta, sem duplicar viagens. | Comunicação das Docas, Viagens |
| US-4 | Como gestor municipal, obtenho o relatório de utilização por freguesia. | Relatórios Municipais |

## 4. Componentes lógicos e responsabilidades

- **Utilizadores** — gere a identificação dos utilizadores e os dados da conta necessários ao acesso e à tarifação.
- **Desbloqueio** — valida e executa o desbloqueio de uma bicicleta.
- **Viagens** — regista e mantém o estado da viagem de um utilizador, e, após o fecho, desencadeia o cálculo da tarifa e a cobrança, se aplicável.
- **Tarifação** — calcula a tarifa aplicável a uma viagem.
- **Cobrança** — processa a cobrança ao utilizador.
- **Manutenção** — recebe reportes manuais e avarias identificadas pela Telemetria, cria ordens pendentes de avaliação pelos técnicos e gere o registo das intervenções e o fecho das ordens.
- **Consulta de Estações** — disponibiliza o estado das estações, incluindo bicicletas disponíveis e docas livres.
- **Relatórios Municipais** — agrega os dados necessários e produz o relatório mensal para a Câmara.
- **Telemetria** — recebe e processa a telemetria enviada pelas bicicletas elétricas.
- **Histórico de Viagens** — disponibiliza ao utilizador o histórico das viagens realizadas.
- **Faturação** — gera, guarda e disponibiliza as faturas associadas às viagens, com os dados necessários da viagem e da cobrança.
- **Comunicação das Docas** — gere o envio de comandos e a receção de eventos das docas, encaminhando-os para os componentes responsáveis.
- **Planeamento de Redistribuição** — analisa a ocupação das estações e, quando o desequilíbrio ultrapassa o limiar configurado, calcula as quantidades de bicicletas a recolher e entregar em cada estação.
- **Planeamento de Rotas** — calcula e disponibiliza às equipas as rotas para executar as recolhas e entregas previstas no plano de redistribuição.

## 5. Análise de coesão

De forma geral, os componentes definidos apresentam boa coesão, uma vez que cada um concentra responsabilidades relacionadas com uma função específica do sistema.

Por exemplo, Desbloqueio trata apenas do processo de desbloqueio, Viagens concentra o registo e estado das viagens, Tarifação calcula os valores aplicáveis e Manutenção trata dos reportes de avaria e ordens de manutenção.

A separação entre componentes como Viagens, Tarifação, Cobrança, Faturação e Histórico de Viagens evita concentrar responsabilidades distintas num único componente, reduzindo o risco de baixa coesão.

Da mesma forma, Comunicação das Docas, Telemetria, Consulta de Estações, Planeamento de Redistribuição e Planeamento de Rotas têm responsabilidades distintas, apesar de trabalharem sobre informação relacionada com bicicletas e estações.

Utilizadores reúne a identificação e os dados da conta necessários ao acesso e à tarifação. Estas responsabilidades estão relacionadas com a conta do utilizador, enquanto o desbloqueio e o cálculo da tarifa permanecem nos componentes próprios.

A decomposição não foi feita apenas com base nas entidades do domínio, mas sim nos workflows e responsabilidades do sistema, evitando assim a Entity Trap.

## 6. Acoplamento estático e instabilidade

A instabilidade é calculada através de:

**I = CE / (CA + CE)**

onde:

- **CA** corresponde ao número de componentes que dependem do componente;
- **CE** corresponde ao número de componentes de que o componente depende.

As dependências consideradas são:

- Desbloqueio → Utilizadores
- Desbloqueio → Comunicação das Docas
- Comunicação das Docas → Viagens
- Comunicação das Docas → Consulta de Estações
- Viagens → Tarifação
- Viagens → Cobrança
- Tarifação → Utilizadores
- Cobrança → Utilizadores
- Telemetria → Manutenção
- Planeamento de Redistribuição → Consulta de Estações
- Planeamento de Redistribuição → Planeamento de Rotas
- Histórico de Viagens → Viagens
- Faturação → Cobrança
- Faturação → Viagens

| Componente | Depende de | CA | CE | Instabilidade |
|---|---|---:|---:|---:|
| Utilizadores | — | 3 | 0 | 0 |
| Desbloqueio | Comunicação das Docas, Utilizadores | 0 | 2 | 1 |
| Viagens | Tarifação, Cobrança | 3 | 2 | 0,4 |
| Tarifação | Utilizadores | 1 | 1 | 0,5 |
| Cobrança | Utilizadores | 2 | 1 | 0,33 |
| Telemetria | Manutenção | 0 | 1 | 1 |
| Manutenção | — | 1 | 0 | 0 |
| Comunicação das Docas | Viagens, Consulta de Estações | 1 | 2 | 0,67 |
| Consulta de Estações | — | 2 | 0 | 0 |
| Planeamento de Redistribuição | Consulta de Estações, Planeamento de Rotas | 0 | 2 | 1 |
| Planeamento de Rotas | — | 1 | 0 | 0 |
| Histórico de Viagens | Viagens | 0 | 1 | 1 |
| Faturação | Cobrança, Viagens | 0 | 2 | 1 |
| Relatórios Municipais | — | 0 | 0 | N/A |

Valores próximos de 0 indicam componentes mais estáveis, enquanto valores próximos de 1 indicam componentes mais instáveis.

Relatórios Municipais consulta diretamente a base de dados, apenas em leitura, através de queries definidas no próprio componente. Depende, por isso, da estrutura das tabelas consultadas, embora não utilize diretamente o componente Viagens.

## 7. Acoplamento temporal

### Exemplo 1 — Devolução da bicicleta

A confirmação de encaixe da doca tem de ser recebida antes de a viagem poder ser fechada.

### Exemplo 2 — Cobrança da viagem

A viagem tem de estar fechada antes de a tarifa poder ser calculada, e a tarifa tem de ser calculada antes de a cobrança ser efetuada.

## 8. Conascência

Existe conascência entre os componentes **Tarifação** e **Cobrança**, porque a Cobrança utiliza o valor calculado pela Tarifação, recebido através de Viagens.

Os dois componentes têm de concordar sobre a representação e o significado desse valor, nomeadamente a moeda e a unidade do montante, como euros ou cêntimos. Uma alteração nesta convenção pode exigir alterações em ambos os componentes, mesmo sem existir uma dependência direta entre eles.

## 9. Iteração de reestruturação

### Primeira iteração de reestruturação

Na decomposição inicial, os eventos enviados pelas docas não tinham um componente próprio e várias dependências entre componentes ainda não estavam definidas.

Durante o mapeamento das user stories e a análise dos fluxos, verificou-se que a responsabilidade de receber e gerir eventos das docas não pertencia ao componente Telemetria, que trata os dados enviados pelas bicicletas elétricas, nem ao componente Viagens.

Por esse motivo, foi criado o componente **Comunicação das Docas**, responsável pela interação com as docas e pela receção dos respetivos eventos.

A análise permitiu também clarificar várias dependências entre componentes. Desbloqueio passou a depender de Comunicação das Docas para executar o desbloqueio, enquanto Comunicação das Docas passou a comunicar com Viagens para iniciar ou fechar viagens e com Consulta de Estações para atualizar a ocupação das estações.

No fluxo principal, Viagens desencadeia o cálculo da tarifa através de Tarifação e Tarifação desencadeia posteriormente a Cobrança.

Foram também explicitadas outras dependências, como Telemetria → Manutenção, Redistribuição → Consulta de Estações e Viagens, Histórico de Viagens → Viagens, Faturação → Viagens e Cobrança, e Relatórios Municipais → Viagens.

Esta iteração permitiu tornar mais claras as responsabilidades de cada componente e as relações entre eles, reduzindo ambiguidade e preparando a arquitetura para as regras de dependência.

### Segunda iteração de reestruturação

#### Utilizadores

A análise do acesso por app ou cartão Navegante e da tarifação para assinantes e ocasionais revelou uma responsabilidade ainda não atribuída explicitamente.

Foi criado o componente **Utilizadores** para concentrar a identificação e os dados da conta necessários ao acesso e à tarifação. Desbloqueio e Tarifação passam a consultar este componente, evitando duplicar esse conhecimento.

#### Coordenação da tarifação e cobrança

Na versão anterior, Tarifação calculava o preço e desencadeava a cobrança. Esta coordenação passou para Viagens, que, após fechar a viagem, solicita o cálculo a Tarifação e, caso o valor seja superior a zero, solicita o pagamento a Cobrança. A coordenação foi atribuída a Viagens porque estas operações integram o processo de conclusão de uma viagem, enquanto a responsabilidade de Tarifação é calcular o preço.

Foi substituída a dependência Tarifação → Cobrança por Viagens → Cobrança. Esta alteração melhora a coesão de Tarifação, que fica responsável apenas pelo cálculo do preço. Como trade-off, Viagens passa a ter mais uma dependência direta e assume a coordenação destas duas operações.

#### Tratamento de avarias e ordens de manutenção

Foi clarificado o workflow de manutenção para distinguir reportes manuais de avarias identificadas pela Telemetria. Definiu-se que as ordens são criadas pendentes de avaliação pelo técnico, que determina a necessidade de intervenção, ficando o resultado registado no fecho.

Estas responsabilidades permanecem no componente Manutenção por integrarem o mesmo processo de tratamento de avarias, sem necessidade de criar um componente adicional ou alterar as dependências existentes.

#### Separação do planeamento de redistribuição e de rotas

Redistribuição foi dividido em Planeamento de Redistribuição, que determina as quantidades a recolher e entregar, e Planeamento de Rotas, que calcula e disponibiliza os percursos. Esta separação permite evoluir os dois cálculos de forma independente, com o trade-off de acrescentar um componente e um contrato entre ambos.

Foi retirada a dependência de Viagens, pois o planeamento adotado utiliza apenas a ocupação disponibilizada por Consulta de Estações, sem antecipar a procura através do histórico de viagens.

#### Acesso ao meio de pagamento

Foi acrescentada a dependência Cobrança → Utilizadores para obter a referência do cartão associado ao utilizador, quando esse método é escolhido. No pagamento por MB WAY, os dados necessários são fornecidos no pedido de pagamento, sem essa consulta.

#### Acesso aos dados para relatórios municipais

Foi retirada a dependência Relatórios Municipais → Viagens. As consultas necessárias aos relatórios passam a ser realizadas diretamente na base de dados, apenas em leitura, pelo próprio componente. A decisão e os respetivos trade-offs são documentados num ADR.

## 10. Lei de Deméter

A arquitetura procura limitar o conhecimento entre componentes, fazendo com que cada componente interaja apenas com aqueles de que necessita diretamente.

Por exemplo, o componente Desbloqueio comunica com Comunicação das Docas para executar o desbloqueio, não conhecendo diretamente o componente Viagens. Depois da confirmação da doca, Comunicação das Docas informa Viagens para iniciar a viagem.

Da mesma forma, Viagens interage diretamente com Tarifação para obter o valor a pagar e com Cobrança para executar o pagamento quando o valor é superior a zero. Ambos são colaboradores diretos, sem ser necessário aceder à estrutura interna de um para chegar ao outro.

Desta forma, cada componente conhece apenas os colaboradores diretamente necessários à sua responsabilidade, reduzindo o acoplamento.