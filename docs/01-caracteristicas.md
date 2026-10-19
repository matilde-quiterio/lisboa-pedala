# 01 - Características Arquiteturais

## 1. Características candidatas

| Característica | Categoria | Implícita? | Origem no enunciado | Justificação |
|---|---|---|---|---|
| Availability | Operacional | Sim | "O contrato de concessão aplica uma multa por cada hora em que mais de 10% das estações não conseguem desbloquear bicicletas." | O serviço de desbloqueio tem de permanecer disponível. |
| Robustness | Operacional | Sim | "As docas comunicam por rede móvel e há zonas onde a rede falha com frequência." | O sistema deve lidar com falhas de ligação durante a execução. |
| Recoverability | Operacional | Sim | "Cada doca guarda até 24 h de eventos localmente." | O sistema deve recuperar após falhas sem perder ou duplicar eventos. |
| On-demand elasticity | Cloud | Sim | "Em eventos (...) a procura em algumas estações multiplica por 4." | O sistema deve adaptar-se a picos temporários de procura. |
| Archivability | Transversal | Não | "As faturas são comunicadas à Autoridade Tributária e guardadas durante 10 anos." | Há uma obrigação explícita de retenção dos dados fiscais. |
| Privacy | Transversal | Não | "O percurso de cada viagem é dado pessoal (RGPD)." | Os dados de percurso têm de ser protegidos. |
| Configurability | Estrutural | Sim | "Duas câmaras vizinhas mostraram interesse em usar a plataforma com tarifários próprios." | A plataforma deve suportar tarifários diferentes sem reescrever o núcleo. |

## 2. Característica composta

### Resiliência operacional

A resiliência operacional é relevante no Lisboa Pedala porque as docas dependem de rede móvel, podem ficar temporariamente sem comunicação e o serviço de desbloqueio tem implicações contratuais.

Decompõe-se em:

- **Availability** — o serviço de desbloqueio deve permanecer disponível.
- **Robustness** — o sistema deve tolerar falhas de ligação durante a execução.
- **Recoverability** — após uma falha, os eventos acumulados devem ser recuperados sem perdas ou duplicações.

## 3. Top 3 características arquiteturais

- Availability
- Robustness
- Configurability

## 4. Cenários concretos das Top 3

### Availability

Durante a hora de ponta, um utilizador tenta desbloquear uma bicicleta numa estação. O serviço de desbloqueio deve permanecer disponível, de forma a que menos de 10% das estações estejam impossibilitadas de realizar desbloqueios.

### Robustness

Uma doca perde temporariamente a ligação à rede móvel. A falha de comunicação não deve provocar perda de informação: os eventos devem ser guardados localmente e tratados quando a ligação for restabelecida.

### Configurability

Uma nova câmara municipal começa a utilizar a plataforma com um tarifário diferente. O tarifário desse município deve poder ser configurado sem ser necessário alterar a lógica central do sistema.

## 5. Outras características consideradas

- Recoverability
- On-demand elasticity
- Archivability
- Privacy