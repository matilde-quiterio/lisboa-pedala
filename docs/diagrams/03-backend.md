# C4 — Nível 3: Componentes do Backend Principal

Este diagrama apresenta os componentes internos do Backend Principal e as dependências permitidas entre eles.

```mermaid
flowchart TB
    subgraph BE["Backend Principal"]
        U["Utilizadores"]
        D["Desbloqueio"]
        CD["Comunicação das Docas"]
        V["Viagens"]
        T["Tarifação"]
        C["Cobrança"]
        F["Faturação"]
        H["Histórico de Viagens"]
        CE["Consulta de Estações"]
        PR["Planeamento de Redistribuição"]
        RT["Planeamento de Rotas"]
        RM["Relatórios Municipais"]

        D -->|Valida utilizador| U
        D -->|Solicita preparação da viagem| V
        D -->|Solicita destrancamento| CD

        CD -->|Encaminha eventos da utilização| V
        CD -->|Atualiza ocupação| CE

        V -->|Solicita cálculo da tarifa| T
        V -->|Solicita pagamento| C
        V -->|Solicita emissão de fatura| F

        T -->|Consulta passe e tipo de utilizador| U
        C -->|Obtém referência do cartão, se aplicável| U

        H -->|Consulta viagens| V

        PR -->|Consulta ocupação| CE
        PR -->|Solicita cálculo de rotas| RT
    end

    DB[("Base de dados partilhada")]
    DOCAS["Estações e docas simuladas"]

    CD -->|Comandos de destrancamento| DOCAS
    DOCAS -->|Resultados e eventos físicos| CD

    RM -->|Leitura apenas| DB

    classDef componente fill:#174a73,stroke:#103550,color:#fff;
    classDef equipamento fill:#ffe0b2,stroke:#b36b00,color:#111;

    class U,D,CD,V,T,C,F,H,CE,PR,RT,RM,DB componente;
    class DOCAS equipamento;
```

## Legenda

- **Azul-escuro:** componentes e armazenamento internos do Lisboa Pedala.
- **Laranja-claro:** equipamentos que comunicam com a plataforma.
- **Retângulo com o nome Backend Principal:** fronteira do contentor detalhado.
- **Cilindro:** base de dados.
- **Seta:** dependência ou comunicação no sentido indicado.

As dependências entre componentes correspondem às regras `allowed-to-use` definidas em `ARCHITECTURE.md`. As interações diretas entre estes componentes usam comunicação síncrona request/response. Os eventos físicos das docas são recebidos em momentos distintos e encaminhados por Comunicação das Docas.

Desbloqueio coordena o acesso. Solicita a Viagens a verificação da exclusividade do utilizador e da bicicleta e a criação do registo pendente antes de solicitar o destrancamento.

Os resultados e eventos físicos enviados pelas docas incluem falhas de destrancamento, retirada, devolução, expiração do prazo com bloqueio confirmado e dados de ocupação. Comunicação das Docas encaminha os resultados da utilização para Viagens e as atualizações de ocupação para Consulta de Estações.

Viagens gere os estados do registo. A retirada confirmada marca o início da viagem e o encaixe confirmado marca o fim, usando os instantes físicos registados pelas docas. Após o fecho, coordena Tarifação, Cobrança e Faturação, cuja lógica permanece nos respetivos componentes.

Relatórios Municipais consulta diretamente a base de dados partilhada apenas em leitura. A ligação à BD é destacada para explicitar esta decisão; os acessos de persistência dos restantes componentes foram omitidos para simplificar o diagrama.