# US-2 — Segunda tentativa: Telemetria

## Pedido e contexto

Ferramenta: Gemini  
Modelo: 3.1 Pro

Ficheiros fornecidos:

- `ARCHITECTURE.md`
- `docs/02-componentes.md`
- `docs/adr/ADR-004.md`
- `docs/adr/ADR-005.md`

### Pedido enviado

Quero implementar a US-2: como técnico, recebo uma ordem de manutenção quando uma bicicleta reporta uma avaria.

Esta é uma segunda tentativa. Usa as versões atuais dos ficheiros fornecidos.

Na primeira tentativa, Manutenção importava Broker e MensagemAvaria de Telemetria, criando a dependência proibida Manutenção → Telemetria. A fitness function `test_allowed_to_use` detetou essa violação; `test_no_circular_dependencies` passou. O broker também entregava as mensagens através de callbacks síncronos. Revê essa implementação e respeita o modelo assíncrono definido no ADR-005.

Gera os componentes Telemetria e Manutenção em Python 3.11+, respeitando as responsabilidades, contratos e dependências permitidas nos documentos. Não cries uma dependência de Manutenção para Telemetria, incluindo através de imports de tipos ou modelos.

Usa SQLite para persistir as ordens entre execuções. Implementa as responsabilidades de Telemetria e Manutenção definidas nos documentos, sem inventar regras de negócio ou alterar decisões arquiteturais. Se faltar alguma decisão necessária, assinala-a antes de a assumir.

Usa esta estrutura:

- `src/manutencao/telemetria.py`
- `src/manutencao/manutencao.py`
- `main.py` para demonstrar a US-2
- `tests/test_us2_manutencao.py` para os testes funcionais

Mantém `tests/architecture/` para os testes de arquitetura existentes; não os alteres.

Inclui testes funcionais para:

- uma avaria gerar uma ordem pendente de avaliação;
- o reenvio da mesma mensagem não criar uma ordem duplicada;
- o técnico avaliar a ordem e registar o resultado conforme o ciclo de vida definido;
- a ordem continuar persistida depois de fechar e reabrir a base de dados.

Indica os ficheiros criados ou alterados e os comandos para executar a CLI e os testes. Distingue os testes que executaste dos que apenas propões executar.

## Avaliação do resultado

**Resultado: parcialmente aceite; integração pendente de revisão do broker.**

`telemetria.py` cria uma mensagem de avaria e publica-a através de um callback. Não importa diretamente Manutenção, pelo que não cria a dependência proibida identificada na primeira tentativa.

A CLI usa uma `queue.Queue` com um worker para processar as mensagens de forma assíncrona durante a execução. Contudo, a fila é apenas em memória e não implementa a persistência das mensagens nem a confirmação após processamento definidas no ADR-005. A limitação foi identificada em revisão humana; as fitness functions não verificam o comportamento do broker.

A CLI foi executada com `python -m src.main` e demonstrou a criação de uma ordem pendente. Os testes de arquitetura passaram; após uma correção manual no repositório SQLite, o utilizador confirmou que os testes funcionais também passaram.

A implementação cobre a publicação de avarias necessária à US-2. O processamento geral da telemetria e a atualização do estado da bicicleta descritos no workflow de telemetria não foram demonstrados por estes testes.