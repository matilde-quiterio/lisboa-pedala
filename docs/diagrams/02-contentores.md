# C4 — Nível 2: Contentores

O diagrama mostra as principais aplicações e armazenamentos do Lisboa Pedala e as comunicações entre eles.

```mermaid
flowchart TB
    P["Pessoas e equipas"]
    D["Estações e docas simuladas"]
    B["Bicicletas elétricas"]

    subgraph LP["Lisboa Pedala"]
        A["Aplicação cliente:
        permite interagir com a plataforma"]

        BE["Backend principal:
        executa as operações de viagens, estações, redistribuição e reporting municipal"]

        MF["Manutenção da Frota:
        recebe telemetria e gere avarias e intervenções"]

        DB[("Base de dados partilhada:
        guarda os dados da plataforma")]

        Q["Broker de mensagens:
        suporta comunicação assíncrona
        entre Telemetria e Manutenção"]

        A -->|Operações da plataforma| BE
        A -->|Reportes e ordens| MF

        BE ---->|Lê e escreve| DB
        MF ---->|Lê e escreve| DB

        MF -.->|Publica avarias| Q
        Q -.->|Entrega avarias| MF
    end

    P -->|Utilizam| A
    BE -->|Pedido de desbloqueio| D
    D -->|Confirma desbloqueio e devolução; informa ocupação| BE
    B -->|Telemetria| MF

    classDef pessoa fill:#e8f0fe,stroke:#2457a7,color:#111;
    classDef interno fill:#174a73,stroke:#103550,color:#fff;
    classDef equipamento fill:#ffe0b2,stroke:#b36b00,color:#111;

    class P pessoa;
    class A,BE,MF,DB,Q interno;
    class D,B equipamento;
```

## Legenda

- **Azul-claro:** pessoas ou equipas que utilizam a plataforma.
- **Azul-escuro:** aplicações e armazenamentos internos do Lisboa Pedala.
- **Laranja-claro:** equipamentos que comunicam com a plataforma.
- **Retângulo com o nome Lisboa Pedala:** fronteira do sistema.
- **Cilindro:** base de dados.
- **Seta contínua:** pedido, acesso a dados ou envio de informação, conforme o texto.
- **Seta tracejada:** comunicação assíncrona através do broker.

As chamadas da aplicação cliente e as comunicações com as docas são síncronas. As docas recebem comandos de desbloqueio e enviam confirmações de desbloqueio e devolução e dados de ocupação.

No backend principal, Reporting apenas lê os dados operacionais.

Telemetria recebe os dados das bicicletas e atualiza o respetivo estado. Quando identifica uma avaria, publica uma mensagem no broker para processamento por Manutenção. Ambos os componentes pertencem à aplicação Manutenção da Frota.