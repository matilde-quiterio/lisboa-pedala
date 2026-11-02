# C4 — Nível 1: Contexto

O diagrama apresenta quem utiliza o Lisboa Pedala e os equipamentos com que comunica, sem detalhar a organização interna da plataforma.

```mermaid
flowchart TB
    U["Utilizador"]
    T["Técnico de manutenção"]
    E["Equipa de redistribuição"]
    G["Gestor municipal"]

    S["Lisboa Pedala"]

    D["Estações e docas simuladas"]
    B["Bicicletas elétricas"]

    U -->|Consulta mapa de bicicletas disponíveis e docas livres, realiza viagens e consulta histórico e faturas| S
    T -->|Consulta e atualiza ordens de manutenção| S
    E -->|Consulta planos de recolha, entrega e rotas| S
    G -->|Consulta relatórios municipais| S

    S -->|Envia comandos de destrancamento| D
    D -->|Enviam resultados de destrancamento, eventos de retirada e devolução e dados de ocupação| S
    B -->|Enviam telemetria| S

    classDef pessoa fill:#e8f0fe,stroke:#2457a7,color:#111;
    classDef sistema fill:#174a73,stroke:#103550,color:#fff;
    classDef equipamento fill:#ffe0b2,stroke:#b36b00,color:#111;

    class U,T,E,G pessoa;
    class S sistema;
    class D,B equipamento;
```

## Legenda

- **Azul-claro:** pessoas ou equipas que utilizam a plataforma.
- **Azul-escuro:** sistema Lisboa Pedala.
- **Laranja-claro:** equipamentos que comunicam com a plataforma.
- **Seta:** interação no sentido indicado, descrita pelo respetivo texto.

As docas são simuladas. Não são representados serviços externos de pagamentos ou de validação do cartão Navegante, pois essas operações também são simuladas.