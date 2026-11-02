# C4 — Nível 3: Componentes de Manutenção da Frota

Este diagrama apresenta os componentes internos da aplicação Manutenção da Frota e a comunicação assíncrona utilizada no tratamento de avarias identificadas através da telemetria.

```mermaid
flowchart LR

    B["Bicicletas elétricas"]

    subgraph MF["Manutenção da Frota"]
        T["Telemetria"]
        M["Manutenção"]
    end

    Q["Broker de mensagens"]
    DB[("Base de dados partilhada")]

    B -->|Envia telemetria| T

    T -.->|Publica mensagem de avaria| Q
    Q -.->|Entrega mensagem| M

    T -->|Lê e escreve estado| DB
    M -->|Lê e escreve ordens e intervenções| DB

    classDef componente fill:#174a73,stroke:#103550,color:#fff;
    classDef equipamento fill:#ffe0b2,stroke:#b36b00,color:#111;
    classDef infraestrutura fill:#e8f0fe,stroke:#2457a7,color:#111;

    class T,M componente;
    class B equipamento;
    class Q,DB infraestrutura;
```

## Legenda

- **Azul-escuro:** componentes internos da aplicação Manutenção da Frota.
- **Laranja-claro:** equipamento externo.
- **Azul-claro:** infraestrutura e armazenamento partilhado.
- **Seta contínua:** envio ou acesso direto a dados.
- **Seta tracejada:** comunicação assíncrona através do broker.

As bicicletas elétricas enviam telemetria para o componente Telemetria.

Quando a Telemetria identifica uma avaria, publica uma mensagem no broker. O componente Manutenção recebe posteriormente essa mensagem e pode criar uma ordem de manutenção.

A comunicação `Telemetria → Manutenção` é, por isso, assíncrona e não exige que Telemetria espere pela criação da ordem.