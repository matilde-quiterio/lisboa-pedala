# US-2 — Segunda tentativa: Manutenção

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

**Resultado: parcialmente aceite; integração pendente de revisão do ciclo de vida da ordem.**

A dependência proibida Manutenção → Telemetria foi corrigida. A implementação persiste as ordens em SQLite e o teste de reenvio sequencial verifica que a mesma mensagem não cria uma segunda ordem.

Na primeira execução dos testes funcionais, a limpeza da base de dados falhou com `PermissionError` no Windows. A revisão do código identificou que as ligações SQLite não eram fechadas explicitamente. Com assistência do ChatGPT, apliquei uma correção usando `contextlib.closing`. Depois da alteração, todos os testes passaram, conforme confirmação do utilizador. O problema foi revelado pelo teste funcional e a causa foi identificada na revisão do código; não foi detetado pelas fitness functions.

A revisão humana também identificou que `OrdemManutencao` guarda apenas `resultado`. A avaliação do técnico e os detalhes da intervenção, quando aplicável, não são guardados separadamente, apesar de a arquitetura determinar o registo da avaliação, da intervenção e do resultado final. O estado `EM_INTERVENCAO` está definido, mas não é usado. Os testes funcionais existentes não detetam esta lacuna.

A CLI foi executada com `python -m src.main` e demonstrou a criação de uma ordem pendente.