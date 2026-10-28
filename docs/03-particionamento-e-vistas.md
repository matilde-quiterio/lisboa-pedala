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

As dependências dentro do mesmo domínio são permitidas quando correspondem às responsabilidades definidas na vista de componentes.

As dependências entre domínios são restritas às seguintes relações:

- **Operação de Viagens** pode usar **Operação de Estações**, nomeadamente para obter informação relacionada com docas, levantamento e devolução de bicicletas.
- **Operação de Estações** pode usar **Operação de Viagens**, quando necessita de informação sobre utilização das estações para apoiar a redistribuição.
- **Reporting Municipal** pode usar **Operação de Viagens**, para obter dados necessários à produção de relatórios.
- **Manutenção da Frota** não depende funcionalmente dos restantes domínios.

Não são permitidas outras dependências entre domínios.

Adicionalmente:

- **Reporting Municipal** apenas consome informação e não deve ser usado pelos restantes domínios.
- As dependências devem seguir as responsabilidades definidas para cada componente, evitando acessos diretos desnecessários entre componentes.
- A comunicação assíncrona através do broker não altera estas regras de dependência lógica; apenas muda o mecanismo de comunicação.
## 4. Vista de Componentes e Conectores

A vista de componentes e conectores representa o fluxo principal **desbloquear → devolver → cobrar**.

```mermaid
flowchart LR
    D[Desbloqueio] --> CD[Comunicação das Docas]
    CD --> V[Viagens]
    V --> T[Tarifação]
    T --> C[Cobrança]

    CD -->|confirma devolução| V
```

### Legenda

As comunicações representadas neste fluxo são **síncronas (request/response)**, uma vez que cada passo depende diretamente da conclusão do anterior.

- **Desbloqueio → Comunicação das Docas**: é enviado o pedido de desbloqueio e o utilizador necessita de uma resposta imediata.
- **Comunicação das Docas → Viagens**: após a confirmação do desbloqueio físico da bicicleta, é iniciada a viagem.
- **Comunicação das Docas → Viagens (devolução)**: a doca confirma a devolução da bicicleta e a viagem é terminada.
- **Viagens → Tarifação**: após o fim da viagem, é calculado o valor a pagar.
- **Tarifação → Cobrança**: o valor calculado é enviado para processamento da cobrança.

Optou-se por comunicação síncrona neste fluxo por se tratar do caminho principal da operação, em que existe dependência direta entre os passos e necessidade de consistência imediata.

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

### Responsabilidade pelos componentes

A responsabilidade pelos componentes foi distribuída por domínio, de forma a manter cada elemento do grupo responsável por conjuntos funcionais coerentes.

| Domínio | Componente | Responsável |
|---|---|---|
| Operação de Viagens | Desbloqueio | Matilde |
| Operação de Viagens | Viagens | Matilde |
| Operação de Viagens | Tarifação | Matilde |
| Operação de Viagens | Cobrança | Matilde |
| Operação de Viagens | Histórico de Viagens | Matilde |
| Operação de Viagens | Faturação | Matilde |
| Reporting Municipal | Relatórios Municipais | Matilde |
| Operação de Estações | Comunicação das Docas | João |
| Operação de Estações | Consulta de Estações | João |
| Operação de Estações | Redistribuição | João |
| Manutenção da Frota | Telemetria | João |
| Manutenção da Frota | Manutenção | João |

Esta distribuição segue o particionamento por domínio e evita que a responsabilidade sobre componentes fortemente relacionados fique fragmentada entre os elementos do grupo.