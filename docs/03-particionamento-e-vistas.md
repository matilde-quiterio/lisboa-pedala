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

## 4. Vista de Componentes e Conectores

A vista de componentes e conectores representa as principais interações entre os componentes durante a execução do sistema.

Foram distinguidas comunicações síncronas, usadas quando é necessária uma resposta imediata, e comunicações assíncronas, usadas quando o processamento pode ocorrer sem bloquear o fluxo principal.

O componente **Desbloqueio** comunica de forma síncrona com **Comunicação das Docas**, uma vez que o utilizador precisa de saber imediatamente se a bicicleta foi desbloqueada com sucesso.

Após a confirmação física do desbloqueio, **Comunicação das Docas** pode emitir um evento que permite ao componente **Viagens** iniciar a viagem.

Quando uma viagem termina, **Viagens** comunica com **Tarifação** para calcular o respetivo valor. **Tarifação** comunica depois com **Cobrança**, que executa o pagamento quando aplicável.

Após uma cobrança bem-sucedida, pode ser emitido um evento para **Faturação**, permitindo gerar a respetiva fatura sem bloquear o fluxo principal da viagem.

O componente **Viagens** envia também informação para **Histórico de Viagens**, preferencialmente de forma assíncrona, de modo a que o registo histórico não aumente o tempo necessário para concluir uma viagem.

A informação proveniente das docas é utilizada por **Consulta de Estações** para manter atualizado o número de bicicletas e lugares disponíveis. Esta informação, juntamente com dados de utilização provenientes de **Viagens**, é usada por **Redistribuição** para apoiar decisões de movimentação de bicicletas entre estações.

O componente **Telemetria** envia dados de forma assíncrona para **Manutenção**, uma vez que a recolha frequente de informação das bicicletas elétricas não deve bloquear a operação normal do sistema.

Por fim, **Relatórios Municipais** utiliza dados agregados provenientes de **Viagens**, podendo este processamento ser realizado de forma assíncrona ou periódica, uma vez que não pertence ao caminho crítico da operação do serviço.

## 5. Vista de Alocação

A vista de alocação representa a distribuição dos principais elementos do sistema pela infraestrutura onde são executados.

A aplicação cliente é executada nos dispositivos dos utilizadores e comunica com o sistema através da Internet.

O sistema possui um **backend principal**, onde ficam os domínios de:

- Operação de Viagens;
- Operação de Estações;
- Reporting Municipal.

Estes domínios permanecem no mesmo deploy, embora separados internamente em módulos. Esta opção evita introduzir complexidade distribuída desnecessária, uma vez que Operação de Viagens e Operação de Estações colaboram frequentemente e são afetadas por períodos de maior utilização semelhantes.

O domínio de **Manutenção da Frota** é executado separadamente do backend principal e contém os componentes de Telemetria e Manutenção. Esta separação deve-se ao perfil operacional diferente deste domínio, uma vez que recebe e processa continuamente dados provenientes das bicicletas elétricas.

O sistema utiliza uma **base de dados partilhada** entre o backend principal e o domínio de Manutenção da Frota. Apesar de esta opção aumentar algum acoplamento entre os dois, reduz a complexidade associada à sincronização, consistência e duplicação de dados entre diferentes bases de dados.

É também utilizado um **broker de mensagens partilhado**, responsável pelas comunicações assíncronas do sistema. Entre os fluxos que podem utilizar este broker encontram-se:

- Telemetria → Manutenção;
- Viagens → Histórico de Viagens;
- Cobrança → Faturação;
- Viagens → Relatórios Municipais.

Foi escolhido um único broker para evitar aumentar a complexidade de infraestrutura com vários mecanismos de mensagens independentes.

As **estações e docas** estão distribuídas fisicamente pela cidade e comunicam com o backend principal. Esta comunicação é utilizada em operações como desbloqueio de bicicletas, levantamento, devolução e atualização do estado das estações.

As **bicicletas elétricas** enviam periodicamente dados de telemetria, que são tratados pelo domínio de Manutenção da Frota.

O backend comunica ainda com um **sistema de pagamentos externo**, responsável pelo processamento das cobranças associadas às viagens.

### Decisões de alocação

As principais decisões tomadas foram:

- manter Operação de Viagens, Operação de Estações e Reporting Municipal no mesmo backend principal;
- separar o domínio de Manutenção da Frota devido ao seu perfil de carga diferente;
- utilizar uma base de dados partilhada;
- utilizar um único broker de mensagens para os fluxos assíncronos;
- manter as comunicações síncronas apenas nos fluxos em que é necessária uma resposta imediata.

Esta solução procura equilibrar separação de responsabilidades, simplicidade operacional e capacidade de evolução futura, evitando introduzir complexidade distribuída sem uma necessidade clara.