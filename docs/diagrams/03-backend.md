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
        D -->|Solicita desbloqueio| CD

        CD -->|Informa início e devolução| V
        CD -->|Atualiza ocupação| CE

        V -->|Solicita cálculo da tarifa| T
        V -->|Solicita pagamento| C
        V -->|Solicita emissão de fatura| F

        T -->|Consulta dados do utilizador| U
        C -->|Obtém referência do cartão, quando aplicável| U

        H -->|Consulta viagens| V

        PR -->|Consulta ocupação| CE
        PR -->|Solicita cálculo de rotas| RT
    end

    DB[("Base de dados partilhada")]
    DOCAS["Estações e docas simuladas"]

    CD -->|Envia comandos| DOCAS
    DOCAS -->|Confirma desbloqueios, devoluções e ocupação| CD

    RM -->|Leitura apenas| DB

    classDef componente fill:#174a73,stroke:#103550,color:#fff;
    classDef equipamento fill:#ffe0b2,stroke:#b36b00,color:#111;
    classDef dados fill:#e8f0fe,stroke:#2457a7,color:#111;

    class U,D,CD,V,T,C,F,H,CE,PR,RT,RM componente;
    class DOCAS equipamento;
    class DB dados;
```

## Legenda

- **Azul-escuro:** componentes internos do Backend Principal.
- **Laranja-claro:** equipamentos externos simulados.
- **Azul-claro/cilindro:** armazenamento de dados.
- **Seta:** dependência ou comunicação no sentido indicado.

As dependências apresentadas correspondem às regras `allowed-to-use` definidas em `ARCHITECTURE.md`.

O componente Viagens coordena o fecho da viagem, a tarifação, a cobrança e a faturação, mas cada uma destas responsabilidades permanece no respetivo componente.

Relatórios Municipais não depende dos restantes componentes lógicos. Consulta diretamente a base de dados partilhada apenas em leitura.